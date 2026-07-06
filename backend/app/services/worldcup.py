"""World Cup data service — fetches and caches match data from football-data.org."""

import logging
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory cache: {match_id: MatchResponse}
_match_cache: dict = {}
_cache_updated_at: datetime | None = None
CACHE_TTL_SECONDS = 60


async def fetch_upcoming_matches() -> list[dict]:
    """Fetch World Cup matches from football-data.org."""
    if not settings.FOOTBALL_DATA_API_KEY:
        logger.warning("FOOTBALL_DATA_API_KEY not set — returning placeholder matches")
        return _placeholder_matches()

    url = f"https://api.football-data.org/v4/competitions/{settings.FOOTBALL_DATA_COMPETITION_CODE}/matches"
    headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return _parse_matches(data.get("matches", []))
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch match data: %s", exc)
            return _placeholder_matches()


def _parse_matches(raw_matches: list[dict]) -> list[dict]:
    """Parse raw football-data.org response into our schema."""
    parsed = []
    for i, m in enumerate(raw_matches):
        parsed.append({
            "match_id": f"WC2026-M{i + 1}",
            "home_team": _safe_team_name(m.get("homeTeam", {}).get("name")),
            "away_team": _safe_team_name(m.get("awayTeam", {}).get("name")),
            "kickoff_utc": m.get("utcDate", datetime.now(timezone.utc).isoformat()),
            "status": _map_status(m.get("status", "SCHEDULED")),
            "home_score": m.get("score", {}).get("fullTime", {}).get("home"),
            "away_score": m.get("score", {}).get("fullTime", {}).get("away"),
        })
    return parsed


def _safe_team_name(name: str | None) -> str:
    """Fall back to 'TBD' when team name is None (not yet determined)."""
    return name if name else "TBD"


def _map_status(status: str) -> str:
    return {
        "SCHEDULED": "scheduled",
        "TIMED": "scheduled",
        "LIVE": "live",
        "IN_PLAY": "live",
        "PAUSED": "live",
        "FINISHED": "finished",
        "CANCELLED": "cancelled",
        "POSTPONED": "cancelled",
    }.get(status.upper(), "scheduled")


def _placeholder_matches() -> list[dict]:
    """Demo matches for dev without API key."""
    return [
        {
            "match_id": "WC2026-M1",
            "home_team": "Argentina",
            "away_team": "Brazil",
            "kickoff_utc": "2026-07-10T19:00:00Z",
            "status": "scheduled",
            "home_score": None,
            "away_score": None,
        },
        {
            "match_id": "WC2026-M2",
            "home_team": "Germany",
            "away_team": "France",
            "kickoff_utc": "2026-07-11T16:00:00Z",
            "status": "scheduled",
            "home_score": None,
            "away_score": None,
        },
        {
            "match_id": "WC2026-M3",
            "home_team": "Spain",
            "away_team": "England",
            "kickoff_utc": "2026-07-11T19:00:00Z",
            "status": "live",
            "home_score": 1,
            "away_score": 0,
        },
        {
            "match_id": "WC2026-M4",
            "home_team": "Japan",
            "away_team": "Nigeria",
            "kickoff_utc": "2026-07-09T14:00:00Z",
            "status": "finished",
            "home_score": 2,
            "away_score": 2,
        },
    ]
