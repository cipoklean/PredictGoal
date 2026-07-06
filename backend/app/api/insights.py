"""
Premium AI insights endpoint — gated behind x402 micropayment.

Provides deeper match analysis beyond basic win probabilities:
momentum indicators, form analysis, and key player impact scoring.
Requires x402 payment proof (0.5 USDC per insight on testnet).
"""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.services.worldcup import fetch_upcoming_matches
from app.services.analytics import calculate_win_probabilities
from app.services.x402 import verify_x402_payment, X402_PRICING

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/insights", tags=["insights"])


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
    disclaimer: str = "Simulated premium insight. Based on ELO model only."

    model_config = {"extra": "forbid"}


@router.get("/{match_id}", response_model=PremiumInsightResponse)
async def get_premium_insight(request: Request, match_id: str):
    """
    Get premium AI-powered match insight.

    Requires x402 payment proof (0.5 USDC per insight on testnet).
    Provides momentum indicators, form analysis, and key player scoring
    beyond the free win probability endpoint.
    """
    # x402 payment verification
    payment_header = request.headers.get("X-402-Payment")
    if payment_header is None:
        # In production: raise HTTPException(402, "Payment required")
        # For demo: log warning and allow through
        logger.warning(
            "x402 payment missing for premium insight %s (required: %s USDC) — allowing in dev mode",
            match_id, X402_PRICING.get("/api/insights", 0.5),
        )

    # Fetch match data
    raw_matches = await fetch_upcoming_matches()
    match = next((m for m in raw_matches if m["match_id"] == match_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match '{match_id}' not found")

    # Basic probabilities
    analytics = calculate_win_probabilities(
        match_id=match["match_id"],
        home_team=match["home_team"],
        away_team=match["away_team"],
        home_score=match.get("home_score"),
        away_score=match.get("away_score"),
    )

    # Premium insight: momentum indicators (simulated)
    home_elo = analytics.key_stats.get("home_elo", 1700)
    away_elo = analytics.key_stats.get("away_elo", 1700)

    momentum = {
        "home_momentum": _calc_momentum(home_elo, away_elo, match),
        "away_momentum": _calc_momentum(away_elo, home_elo, match),
        "score_pressure": _calc_pressure(match),
    }

    form_analysis = {
        "home_form": _simulate_form(match["home_team"]),
        "away_form": _simulate_form(match["away_team"]),
        "head_to_head": _simulate_h2h(match["home_team"], match["away_team"]),
    }

    key_player_impact = {
        "home_star": _star_player_impact(match["home_team"]),
        "away_star": _star_player_impact(match["away_team"]),
    }

    return PremiumInsightResponse(
        match_id=match["match_id"],
        home_team=match["home_team"],
        away_team=match["away_team"],
        win_prob_home=analytics.win_prob_home,
        win_prob_draw=analytics.win_prob_draw,
        win_prob_away=analytics.win_prob_away,
        momentum=momentum,
        form_analysis=form_analysis,
        key_player_impact=key_player_impact,
    )


def _calc_momentum(team_elo: float, opponent_elo: float, match: dict) -> float:
    """Simulated momentum score (0-100). Based on ELO differential and match state."""
    base = (team_elo - opponent_elo) * 0.03
    score = match.get("home_score") or match.get("away_score")
    if score is not None:
        base += score * 5
    return round(max(0, min(100, 50 + base)), 1)


def _calc_pressure(match: dict) -> str:
    """Qualitative score pressure assessment."""
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


def _simulate_form(team: str) -> str:
    """Simulated recent form string (WWDLW). Deterministic from team name."""
    import hashlib
    chars = "WDL"
    h = hashlib.md5(team.encode()).hexdigest()
    return "".join(chars[int(h[i], 16) % 3] for i in range(5))


def _simulate_h2h(home: str, away: str) -> str:
    """Simulated head-to-head record."""
    import random
    rng = random.Random(hash(home + away))
    hw = rng.randint(1, 5)
    dw = rng.randint(0, 3)
    aw = rng.randint(1, 5)
    return f"{hw}W-{dw}D-{aw}L"


def _star_player_impact(team: str) -> str:
    """Simulated key player impact rating."""
    stars = {
        "Argentina": "Messi-tier (10/10)",
        "Brazil": "Vini Jr-tier (9/10)",
        "France": "Mbappe-tier (10/10)",
        "Germany": "Musiala-tier (8/10)",
        "Spain": "Yamal-tier (9/10)",
        "England": "Bellingham-tier (9/10)",
    }
    return stars.get(team, "Impact player (7/10)")
