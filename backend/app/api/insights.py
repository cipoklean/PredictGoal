"""
Premium AI insights endpoint — gated behind x402 micropayment (3.0 USDC).

Provides deeper match analysis beyond basic win probabilities:
real recent form, head-to-head, momentum, and competition top scorers
— pulled live from football-data.org. When the football-data API is
unavailable (no key / competition data not yet loaded), it falls back to
an ELO-based estimate and reports ``data_source: "simulated"`` so the client
always knows which.
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.worldcup import fetch_upcoming_matches
from app.services.analytics import calculate_win_probabilities
import json

from app.services.x402 import verify_x402_payment, X402_PRICING, build_requirements

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/insights", tags=["insights"])
settings = get_settings()

_FD_BASE = "https://api.football-data.org/v4"

# football-data free tier is ~10 req/min — cache aggressively.
_teams_cache: dict | None = None
_teams_cache_at: datetime | None = None
_TEAMS_TTL = 86400  # 24h

_recent_cache: dict[str, tuple[datetime, list[dict]]] = {}
_RECENT_TTL = 3600  # 1h

_scorers_cache: tuple[datetime, list[dict]] | None = None
_SCORERS_TTL = 3600  # 1h


class PremiumInsightResponse(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    win_prob_home: float
    win_prob_draw: float
    win_prob_away: float
    momentum: dict = Field(default_factory=dict)
    form_analysis: dict = Field(default_factory=dict)
    key_player_impact: dict = Field(default_factory=dict)
    data_source: str = "football-data"
    disclaimer: str = (
        "Real form, head-to-head and top scorers from football-data.org. "
        "Win probabilities from ELO model."
    )

    model_config = {"extra": "forbid"}


# ── football-data helpers ──────────────────────────────────
def _fd_headers() -> dict:
    return {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}


async def _fd_get(client: httpx.AsyncClient, path: str, params: dict | None = None) -> dict:
    """GET a football-data path with retry/backoff for transient errors.

    Retries on connection drops (ReadError/ConnectError), timeouts and HTTP 429
    (rate limit). Persistent failures raise and the caller falls back to the
    ELO estimate (reported as data_source="simulated").
    """
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            r = await client.get(f"{_FD_BASE}{path}", headers=_fd_headers(), params=params)
            if r.status_code == 429:
                # football-data free tier: ~10 req/min. Back off and retry.
                await asyncio.sleep(1.0 * (attempt + 1))
                last_exc = httpx.HTTPStatusError("429", request=r.request, response=r)
                continue
            r.raise_for_status()
            return r.json()
        except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            # Retry on transport drops and 5xx. Do NOT retry 4xx (e.g. 404).
            if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None and exc.response.status_code < 500:
                raise
            last_exc = exc
            await asyncio.sleep(0.5 * (attempt + 1))
    raise last_exc or httpx.HTTPError(f"football-data request failed: {path}")


def _norm(name: str | None) -> str:
    return (name or "").strip().lower()


async def _team_map(client: httpx.AsyncClient) -> dict:
    global _teams_cache, _teams_cache_at
    now = datetime.now(timezone.utc)
    if _teams_cache and _teams_cache_at and (now - _teams_cache_at).total_seconds() < _TEAMS_TTL:
        return _teams_cache
    data = await _fd_get(
        client, f"/competitions/{settings.FOOTBALL_DATA_COMPETITION_CODE}/teams"
    )
    m: dict = {}
    for t in data.get("teams", []):
        tid = t.get("id")
        if not tid:
            continue
        for key in ("name", "shortName", "tla"):
            v = (t.get(key) or "").strip()
            if v:
                m[v.lower()] = tid
    _teams_cache = m
    _teams_cache_at = now
    return m


async def _recent_matches(client: httpx.AsyncClient, team_id: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    cached = _recent_cache.get(str(team_id))
    if cached and (now - cached[0]).total_seconds() < _RECENT_TTL:
        return cached[1]
    data = await _fd_get(
        client, f"/teams/{team_id}/matches",
        params={"status": "FINISHED", "limit": "20"},
    )
    ms = data.get("matches", [])
    _recent_cache[str(team_id)] = (now, ms)
    return ms


async def _scorers(client: httpx.AsyncClient) -> list[dict]:
    global _scorers_cache
    now = datetime.now(timezone.utc)
    if _scorers_cache and (now - _scorers_cache[0]).total_seconds() < _SCORERS_TTL:
        return _scorers_cache[1]
    data = await _fd_get(
        client, f"/competitions/{settings.FOOTBALL_DATA_COMPETITION_CODE}/scorers",
        params={"limit": "30"},
    )
    sc = data.get("scorers", [])
    _scorers_cache = (now, sc)
    return sc


def _score(m: dict, side: str) -> int | None:
    s = m.get("score") or {}
    ft = s.get("fullTime") or {}
    v = ft.get("home" if side == "home" else "away")
    if v is None:
        rt = s.get("regularTime") or {}
        v = rt.get("home" if side == "home" else "away")
    return v


def _result(team_id: int, m: dict) -> str | None:
    hs = _score(m, "home")
    aw = _score(m, "away")
    if hs is None or aw is None:
        return None
    ht = (m.get("homeTeam") or {}).get("id")
    at = (m.get("awayTeam") or {}).get("id")
    if hs == aw:
        return "D"
    if (ht == team_id and hs > aw) or (at == team_id and aw > hs):
        return "W"
    return "L"


def _form(recent: list[dict], team_id: int, n: int = 5) -> list[str]:
    out = []
    for m in recent:
        r = _result(team_id, m)
        if r:
            out.append(r)
        if len(out) >= n:
            break
    return out


def _momentum(recent: list[dict], team_id: int) -> float:
    last5 = []
    for m in recent:
        if _result(team_id, m):
            last5.append(m)
        if len(last5) >= 5:
            break
    if not last5:
        return 50.0
    gf = ga = streak = 0
    for m in last5:
        hs = _score(m, "home") or 0
        aw = _score(m, "away") or 0
        ht = (m.get("homeTeam") or {}).get("id")
        if ht == team_id:
            gf += hs
            ga += aw
        else:
            gf += aw
            ga += hs
        if _result(team_id, m) == "W":
            streak += 1
    score = 50 + (gf - ga) * 4 + streak * 8
    return round(max(0, min(100, score)), 1)


def _h2h(home_id: int, away_id: int, home_recent: list[dict]) -> str:
    hw = dw = aw = 0
    for m in home_recent:
        ht = (m.get("homeTeam") or {}).get("id")
        at = (m.get("awayTeam") or {}).get("id")
        opp = at if ht == home_id else ht
        if opp != away_id:
            continue
        r = _result(home_id, m)
        if r == "W":
            hw += 1
        elif r == "D":
            dw += 1
        else:
            aw += 1
    return f"{hw}W-{dw}D-{aw}L"


def _top_scorer(scorers: list[dict], team_id: int, team_name: str) -> str:
    for s in scorers:
        if (s.get("team") or {}).get("id") == team_id:
            pname = (s.get("player") or {}).get("name", "Unknown")
            goals = s.get("goals", 0)
            return f"{pname} — {goals} goals (competition top scorer)"
    return f"No goals recorded yet ({team_name})"


def _pressure(hm: float, am: float) -> str:
    if hm - am >= 15:
        return "home_dominant"
    if am - hm >= 15:
        return "away_dominant"
    return "balanced"


# ── ELO-based fallback (used when football-data is unavailable) ──
def _simulate_form(team: str) -> str:
    import hashlib

    chars = "WDL"
    h = hashlib.md5(team.encode()).hexdigest()
    return "".join(chars[int(h[i], 16) % 3] for i in range(5))


def _simulate_h2h(home: str, away: str) -> str:
    import random

    rng = random.Random(hash(home + away))
    return f"{rng.randint(0, 4)}W-{rng.randint(0, 3)}D-{rng.randint(0, 4)}L"


def _star_player_impact(team: str) -> str:
    stars = {
        "Argentina": "Messi-tier (10/10)",
        "Brazil": "Vini Jr-tier (9/10)",
        "France": "Mbappe-tier (10/10)",
        "Germany": "Musiala-tier (8/10)",
        "Spain": "Yamal-tier (9/10)",
        "England": "Bellingham-tier (9/10)",
    }
    return stars.get(team, "Impact player (7/10)")


def _momentum_sim(team_elo: int, opp_elo: int, match: dict) -> float:
    base = (team_elo - opp_elo) * 0.03
    sc = match.get("home_score")
    if sc is None:
        sc = match.get("away_score")
    if sc is not None:
        base += sc * 5
    return round(max(0, min(100, 50 + base)), 1)


def _pressure_sim(match: dict) -> str:
    home = match.get("home_score")
    away = match.get("away_score")
    if home is None or away is None:
        return "pre_match"
    diff = home - away
    if abs(diff) >= 2:
        return "dominant"
    if abs(diff) == 1:
        return "tight"
    return "balanced"


@router.get("/{match_id}", response_model=PremiumInsightResponse)
async def get_premium_insight(request: Request, match_id: str):
    """
    Get premium AI-powered match insight.

    Requires x402 payment proof (3.0 USDC per insight on testnet).
    Form, head-to-head, momentum and top scorers are pulled live from
    football-data.org when available; otherwise an ELO-based estimate is used.
    """
    # x402 payment verification (real testnet facilitator)
    payment_header = request.headers.get("X-402-Payment")
    payment_valid = await verify_x402_payment(payment_header, "/api/insights")

    if not payment_valid:
        requirements = await build_requirements("/api/insights")
        headers = (
            {"X-Payment-Requirements": json.dumps(requirements)} if requirements else {}
        )
        raise HTTPException(
            status_code=402,
            detail="Payment required. Send x402 payment proof header. 3.0 USDC per insight.",
            headers=headers,
        )

    # Fetch match data
    raw_matches = await fetch_upcoming_matches()
    match = next((m for m in raw_matches if m["match_id"] == match_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match '{match_id}' not found")

    # Basic probabilities (ELO + Poisson model)
    analytics = calculate_win_probabilities(
        match_id=match["match_id"],
        home_team=match["home_team"],
        away_team=match["away_team"],
        home_score=match.get("home_score"),
        away_score=match.get("away_score"),
    )
    home, away = match["home_team"], match["away_team"]

    momentum: dict = {}
    form_analysis: dict = {}
    key_player_impact: dict = {}
    data_source = "simulated"

    if settings.FOOTBALL_DATA_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                team_map = await _team_map(client)
                hid = team_map.get(_norm(home))
                aid = team_map.get(_norm(away))
                if hid and aid:
                    home_recent = await _recent_matches(client, hid)
                    away_recent = await _recent_matches(client, aid)
                    scorers = await _scorers(client)
                    hm = _momentum(home_recent, hid)
                    am = _momentum(away_recent, aid)
                    momentum = {
                        "home_momentum": hm,
                        "away_momentum": am,
                        "score_pressure": _pressure(hm, am),
                    }
                    form_analysis = {
                        "home_form": "".join(_form(home_recent, hid)) or "N/A",
                        "away_form": "".join(_form(away_recent, aid)) or "N/A",
                        "head_to_head": _h2h(hid, aid, home_recent),
                    }
                    key_player_impact = {
                        "home_star": _top_scorer(scorers, hid, home),
                        "away_star": _top_scorer(scorers, aid, away),
                    }
                    data_source = "football-data"
        except Exception as e:  # noqa: BLE001
            logger.warning("Insights real-data fetch failed; using ELO fallback: %s", e)

    if data_source == "simulated":
        home_elo = analytics.key_stats.get("home_elo", 1700)
        away_elo = analytics.key_stats.get("away_elo", 1700)
        momentum = {
            "home_momentum": _momentum_sim(home_elo, away_elo, match),
            "away_momentum": _momentum_sim(away_elo, home_elo, match),
            "score_pressure": _pressure_sim(match),
        }
        form_analysis = {
            "home_form": _simulate_form(home),
            "away_form": _simulate_form(away),
            "head_to_head": _simulate_h2h(home, away),
        }
        key_player_impact = {
            "home_star": _star_player_impact(home),
            "away_star": _star_player_impact(away),
        }

    disclaimer = (
        "Real form, head-to-head and top scorers from football-data.org. "
        "Win probabilities from ELO model."
        if data_source == "football-data"
        else "Simulated fallback (football-data unavailable) — ELO-based estimates only."
    )

    return PremiumInsightResponse(
        match_id=match["match_id"],
        home_team=home,
        away_team=away,
        win_prob_home=analytics.win_prob_home,
        win_prob_draw=analytics.win_prob_draw,
        win_prob_away=analytics.win_prob_away,
        momentum=momentum,
        form_analysis=form_analysis,
        key_player_impact=key_player_impact,
        data_source=data_source,
        disclaimer=disclaimer,
    )
