"""Prediction API endpoints — place predictions, view history."""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.match import PredictionCreate, PredictionResponse, LeaderboardEntry
from app.services.x402 import X402_PRICING

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predictions", tags=["predictions"])

# In-memory prediction store (replace with DB in production)
_predictions: dict[str, dict] = {}


@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def place_prediction(request: Request, body: PredictionCreate):
    """
    Place a prediction on a match outcome.

    Requires x402 payment header (0.1 USDC per prediction on testnet).
    """
    # In production: verify x402 payment proof
    payment_header = request.headers.get("X-402-Payment")
    if payment_header is None:
        logger.warning("x402 payment missing — allowing in dev mode")

    # Get user address from auth header (stub: use default testnet address)
    user_address = request.headers.get("X-User-Address", "inj1testuser0000000000000000000000")

    # Validate stake is within allowed range
    if body.stake_usdc <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stake must be greater than 0",
        )
    if body.stake_usdc > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum stake is 100 USDC",
        )

    # Create prediction record
    prediction_id = uuid.uuid4()
    tx_hash = f"x402_tx_{prediction_id.hex[:12]}"

    record = {
        "prediction_id": prediction_id,
        "user_address": user_address,
        "match_id": body.match_id,
        "outcome": body.outcome.value,
        "stake_usdc": body.stake_usdc,
        "placed_at": datetime.now(timezone.utc),
        "tx_hash": tx_hash,
        "settled": False,
        "payout_usdc": None,
    }
    _predictions[str(prediction_id)] = record

    logger.info(
        "Prediction placed: id=%s, user=%s, match=%s, outcome=%s, stake=%s USDC",
        prediction_id, user_address, body.match_id, body.outcome.value, body.stake_usdc,
    )

    return PredictionResponse(**record)


@router.get("/me", response_model=list[PredictionResponse])
async def get_my_predictions(request: Request):
    """Get all predictions for the authenticated user."""
    user_address = request.headers.get("X-User-Address", "inj1testuser0000000000000000000000")

    user_predictions = [
        PredictionResponse(**p)
        for p in _predictions.values()
        if p["user_address"] == user_address
    ]
    # Sort by most recent first
    user_predictions.sort(key=lambda p: p.placed_at, reverse=True)
    return user_predictions


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard():
    """Get global prediction leaderboard."""
    # Aggregate by user address
    user_stats: dict[str, dict] = {}

    for p in _predictions.values():
        addr = p["user_address"]
        if addr not in user_stats:
            user_stats[addr] = {
                "user_address": addr,
                "total_wagered": 0.0,
                "total_won": 0.0,
                "predictions_count": 0,
            }
        stats = user_stats[addr]
        stats["total_wagered"] += p["stake_usdc"]
        stats["predictions_count"] += 1
        if p["settled"] and p.get("payout_usdc", 0) > 0:
            stats["total_won"] += p["payout_usdc"]

    # Sort by total won descending
    entries = list(user_stats.values())
    entries.sort(key=lambda e: e["total_won"], reverse=True)

    result = []
    for i, entry in enumerate(entries[:100]):
        win_rate = (
            entry["total_won"] / entry["total_wagered"]
            if entry["total_wagered"] > 0
            else 0.0
        )
        result.append(LeaderboardEntry(
            rank=i + 1,
            user_address=entry["user_address"],
            total_wagered=round(entry["total_wagered"], 2),
            total_won=round(entry["total_won"], 2),
            win_rate=round(win_rate, 4),
            predictions_count=entry["predictions_count"],
        ))

    return result
