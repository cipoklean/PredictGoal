"""Match schemas for the PredictGoal prediction market."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class PredictionOutcome(str, Enum):
    HOME = "home"
    DRAW = "draw"
    AWAY = "away"


# --- Match ---

class MatchBase(BaseModel):
    match_id: str = Field(..., examples=["WC2026-M1"])
    home_team: str
    away_team: str
    kickoff_utc: datetime


class MatchCreate(MatchBase):
    pass


class MatchResponse(MatchBase):
    status: MatchStatus = MatchStatus.SCHEDULED
    home_score: int | None = None
    away_score: int | None = None
    odds_home: float | None = None
    odds_draw: float | None = None
    odds_away: float | None = None

    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    matches: list[MatchResponse]


# --- Prediction ---

class PredictionCreate(BaseModel):
    match_id: str
    outcome: PredictionOutcome
    stake_usdc: float = Field(..., gt=0, le=100.0, description="Stake in USDC (max 100)")

    model_config = {"extra": "forbid"}


class PredictionResponse(BaseModel):
    prediction_id: UUID
    user_address: str
    match_id: str
    outcome: PredictionOutcome
    stake_usdc: float
    placed_at: datetime
    tx_hash: str | None = None
    settled: bool = False
    payout_usdc: float | None = None

    model_config = {"from_attributes": True}


# --- Analytics ---

class MatchAnalytics(BaseModel):
    match_id: str
    win_prob_home: float
    win_prob_draw: float
    win_prob_away: float
    key_stats: dict = Field(default_factory=dict)
    updated_at: datetime


# --- Leaderboard ---

class LeaderboardEntry(BaseModel):
    rank: int
    user_address: str
    total_wagered: float
    total_won: float
    win_rate: float
    predictions_count: int
