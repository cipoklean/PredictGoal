"""Prediction API endpoints — place predictions, view history, settle markets."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.match import PredictionCreate, PredictionResponse, LeaderboardEntry
from app.services.worldcup import fetch_upcoming_matches
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predictions", tags=["predictions"])
settings = get_settings()

# In-memory prediction store (replace with DB in production)
_predictions: dict[str, dict] = {}
_predictions_lock = asyncio.Lock()

# Per-user locks to prevent race conditions on concurrent bets
_user_locks: dict[str, asyncio.Lock] = {}
_user_locks_guard = asyncio.Lock()

# Settled matches (idempotency)
_settled_matches: set[str] = set()
_settlement_locks: dict[str, asyncio.Lock] = {}
_settlement_locks_guard = asyncio.Lock()

# Admin API key for settlement
ADMIN_SETTLE_KEY = settings.ADMIN_SETTLE_KEY


async def _get_user_lock(user_address: str) -> asyncio.Lock:
    """Get or create a per-user asyncio.Lock for atomic operations."""
    async with _user_locks_guard:
        if user_address not in _user_locks:
            _user_locks[user_address] = asyncio.Lock()
        return _user_locks[user_address]


async def _validate_match_for_prediction(match_id: str) -> dict:
    """Validate match exists and hasn't kicked off yet. Returns match dict."""
    raw_matches = await fetch_upcoming_matches()
    match = next((m for m in raw_matches if m["match_id"] == match_id), None)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match '{match_id}' not found",
        )

    # Enforce kickoff cutoff server-side
    match_status = match.get("status", "scheduled")
    if match_status in ("finished", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match '{match_id}' is {match_status} — predictions are closed",
        )

    # For live matches: block predictions (odds change too fast, unfair)
    if match_status == "live":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match '{match_id}' is live — predictions are closed. Place bets before kickoff.",
        )

    kickoff_str = match.get("kickoff_utc")
    if kickoff_str:
        try:
            kickoff = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            if kickoff.tzinfo is None:
                kickoff = kickoff.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if now >= kickoff:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Match '{match_id}' has already kicked off — predictions are closed",
                )
        except (ValueError, TypeError):
            pass  # If we can't parse the date, fall through to accepting

    return match


def _get_user_address(request: Request) -> str:
    """Extract user address from request headers with validation."""
    addr = (request.headers.get("X-User-Address") or "").strip()
    if not addr:
        # In production: require signed message + nonce verification
        # For testnet/demo: accept the header but validate format
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Address header is required",
        )
    if len(addr) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid wallet address format",
        )
    return addr


# ── POST /api/predictions ───────────────────────────────────

@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def place_prediction(request: Request, body: PredictionCreate):
    """
    Place a prediction on a match outcome.

    Requires x402 payment header (0.1 USDC per prediction on testnet).
    Enforces: match exists, hasn't kicked off, valid outcome, per-user atomicity.
    """
    user_address = _get_user_address(request)

    # Validate match exists and is still open for predictions
    match = await _validate_match_for_prediction(body.match_id)

    # x402 payment check (stubbed in dev; real verification in Phase 2)
    payment_header = request.headers.get("X-402-Payment")
    if payment_header is None:
        logger.warning("x402 payment missing for user=%s — allowing in dev mode", user_address)

    # Validate stake bounds (Pydantic already does this, but double-check)
    if body.stake_usdc <= 0:
        raise HTTPException(status_code=400, detail="Stake must be greater than 0")
    if body.stake_usdc > 100:
        raise HTTPException(status_code=400, detail="Maximum stake is 100 USDC")

    # Knockout-stage draw handling: if match is in knockout stage and user bets draw, reject
    # We infer knockout from match ID ranges: WC2026-M49+ are knockout (Round of 32+)
    match_num = int(body.match_id.split("-M")[-1]) if "-M" in body.match_id else 0
    is_knockout = match_num >= 49
    if is_knockout and body.outcome.value == "draw":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draw is not a valid outcome for knockout-stage matches. "
                   "Bet on the winning team (home or away). Extra time + penalties will decide.",
        )

    # Atomic per-user prediction placement (prevents race conditions)
    user_lock = await _get_user_lock(user_address)
    async with user_lock:
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


# ── GET /api/predictions/me ──────────────────────────────────

@router.get("/me", response_model=list[PredictionResponse])
async def get_my_predictions(request: Request):
    """Get all predictions for the authenticated user."""
    user_address = _get_user_address(request)

    async with _predictions_lock:
        user_predictions = [
            PredictionResponse(**p)
            for p in _predictions.values()
            if p["user_address"] == user_address
        ]

    # Sort by most recent first
    user_predictions.sort(key=lambda p: p.placed_at, reverse=True)
    return user_predictions


# ── GET /api/predictions/leaderboard ────────────────────────

@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard():
    """Get global prediction leaderboard (SETTLED predictions only)."""
    async with _predictions_lock:
        all_preds = list(_predictions.values())

    # Only include settled predictions in leaderboard
    user_stats: dict[str, dict] = {}

    for p in all_preds:
        if not p["settled"]:
            continue  # Skip unsettled — only settled predictions count

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
        payout = p.get("payout_usdc") or 0
        if payout > 0:
            stats["total_won"] += payout

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


# ── POST /api/predictions/settle ────────────────────────────

@router.post("/settle")
async def settle_market(request: Request):
    """
    Settle a prediction market after match completion.
    
    ADMIN-ONLY: requires X-Admin-Key header matching ADMIN_SETTLE_KEY.
    Idempotent: calling twice returns same result.
    Reentrancy-safe: per-match asyncio.Lock.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    match_id = body.get("match_id", "")
    home_score = body.get("home_score")
    away_score = body.get("away_score")
    admin_key = request.headers.get("X-Admin-Key", "")

    if not match_id:
        raise HTTPException(status_code=400, detail="match_id is required")

    # ── AUTH GUARD ──
    if ADMIN_SETTLE_KEY and admin_key != ADMIN_SETTLE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid admin key")

    if home_score is None or away_score is None:
        raise HTTPException(status_code=400, detail="home_score and away_score are required")

    # ── IDEMPOTENCY GUARD ──
    if match_id in _settled_matches:
        return {
            "status": "already_settled",
            "match_id": match_id,
            "message": "Market already settled. No duplicate action taken.",
        }

    # ── REENTRANCY GUARD ──
    async with _settlement_locks_guard:
        if match_id not in _settlement_locks:
            _settlement_locks[match_id] = asyncio.Lock()

    async with _settlement_locks[match_id]:
        # Double-check after acquiring lock
        if match_id in _settled_matches:
            return {
                "status": "already_settled",
                "match_id": match_id,
                "message": "Market already settled (caught after lock).",
            }

        # Determine actual outcome
        if home_score > away_score:
            actual_outcome = "home"
        elif home_score < away_score:
            actual_outcome = "away"
        else:
            actual_outcome = "draw"

        # Mark all predictions for this match as settled
        async with _predictions_lock:
            winners = []
            for pid, p in _predictions.items():
                if p["match_id"] == match_id:
                    p["settled"] = True
                    if p["outcome"] == actual_outcome:
                        # Simple payout: stake * 2 (simplified; real would use pool)
                        p["payout_usdc"] = p["stake_usdc"] * 2
                        winners.append(pid)

        _settled_matches.add(match_id)

        logger.info(
            "Market settled: match=%s, score=%d-%d, outcome=%s, winners=%d",
            match_id, home_score, away_score, actual_outcome, len(winners),
        )

        return {
            "status": "settled",
            "match_id": match_id,
            "home_score": home_score,
            "away_score": away_score,
            "actual_outcome": actual_outcome,
            "winners_count": len(winners),
            "message": f"Market for {match_id} settled. Outcome: {actual_outcome}. {len(winners)} winning predictions.",
        }
