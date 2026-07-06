"""Match discovery API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.match import MatchListResponse, MatchResponse, MatchAnalytics
from app.services.worldcup import fetch_upcoming_matches
from app.services.analytics import calculate_win_probabilities

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=MatchListResponse)
async def list_matches():
    """List all World Cup matches with live status."""
    raw_matches = await fetch_upcoming_matches()

    matches = []
    for m in raw_matches:
        analytics = calculate_win_probabilities(
            match_id=m["match_id"],
            home_team=m["home_team"],
            away_team=m["away_team"],
            home_score=m.get("home_score"),
            away_score=m.get("away_score"),
        )
        matches.append(MatchResponse(
            match_id=m["match_id"],
            home_team=m["home_team"],
            away_team=m["away_team"],
            kickoff_utc=m["kickoff_utc"],  # type: ignore[arg-type]
            status=m["status"],  # type: ignore[arg-type]
            home_score=m.get("home_score"),
            away_score=m.get("away_score"),
            odds_home=analytics.win_prob_home,
            odds_draw=analytics.win_prob_draw,
            odds_away=analytics.win_prob_away,
        ))

    return MatchListResponse(matches=matches)


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str):
    """Get a single match by ID."""
    raw_matches = await fetch_upcoming_matches()

    for m in raw_matches:
        if m["match_id"] == match_id:
            analytics = calculate_win_probabilities(
                match_id=m["match_id"],
                home_team=m["home_team"],
                away_team=m["away_team"],
                home_score=m.get("home_score"),
                away_score=m.get("away_score"),
            )
            return MatchResponse(
                match_id=m["match_id"],
                home_team=m["home_team"],
                away_team=m["away_team"],
                kickoff_utc=m["kickoff_utc"],  # type: ignore[arg-type]
                status=m["status"],  # type: ignore[arg-type]
                home_score=m.get("home_score"),
                away_score=m.get("away_score"),
                odds_home=analytics.win_prob_home,
                odds_draw=analytics.win_prob_draw,
                odds_away=analytics.win_prob_away,
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Match '{match_id}' not found",
    )


@router.get("/{match_id}/analytics", response_model=MatchAnalytics)
async def get_match_analytics(match_id: str):
    """Get AI-powered win probabilities and stats for a match."""
    raw_matches = await fetch_upcoming_matches()

    for m in raw_matches:
        if m["match_id"] == match_id:
            return calculate_win_probabilities(
                match_id=m["match_id"],
                home_team=m["home_team"],
                away_team=m["away_team"],
                home_score=m.get("home_score"),
                away_score=m.get("away_score"),
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Match '{match_id}' not found",
    )
