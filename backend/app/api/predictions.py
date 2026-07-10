"""Prediction API endpoints — place predictions, view history, settle markets."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app import store
from app.schemas.match import PredictionCreate, PredictionResponse, LeaderboardEntry
from app.services.worldcup import fetch_upcoming_matches
from app.services.balance import credit as credit_balance, debit as debit_balance
import json

from app.services import x402 as x402_service
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predictions", tags=["predictions"])
settings = get_settings()

# Per-user locks to prevent race conditions on concurrent bets
_user_locks: dict[str, asyncio.Lock] = {}
_user_locks_guard = asyncio.Lock()

# Per-match settlement locks (reentrancy guard)
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

    match_status = match.get("status", "scheduled")
    if match_status in ("finished", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match '{match_id}' is {match_status} — predictions are closed",
        )

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
            pass

    return match


def _get_user_address(request: Request) -> str:
    """Extract user address from request headers with validation."""
    addr = (request.headers.get("X-User-Address") or "").strip()
    if not addr:
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

    # x402 payment verification — enforced when X402_PAYMENT_RECIPIENT is
    # configured (see app/services/x402.py); dev-mode passthrough otherwise.
    payment_header = request.headers.get("X-402-Payment")
    payment_valid = await x402_service.verify_x402_payment(payment_header, "/api/predictions")
    if not payment_valid:
        requirements = await x402_service.build_requirements("/api/predictions")
        headers = (
            {"X-Payment-Requirements": json.dumps(requirements)} if requirements else {}
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment required. Send an x402 payment proof in the X-402-Payment header (2.0 USDC).",
            headers=headers,
        )

    # Validate stake bounds
    if body.stake_usdc <= 0:
        raise HTTPException(status_code=400, detail="Stake must be greater than 0")
    if body.stake_usdc > 100:
        raise HTTPException(status_code=400, detail="Maximum stake is 100 USDC")

    # x402 platform fee (2 USDC per prediction on top of stake)
    x402_fee = 2.0

    # Atomic per-user prediction placement (prevents race conditions)
    user_lock = await _get_user_lock(user_address)
    async with user_lock:
        # Deduct stake + x402 fee from balance (persisted via store)
        total_cost = body.stake_usdc + x402_fee
        try:
            debit_balance(user_address, total_cost)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # Create prediction record
        prediction_id = uuid.uuid4()
        tx_hash = f"x402_tx_{prediction_id.hex[:12]}"

        record = {
            "prediction_id": str(prediction_id),
            "user_address": user_address,
            "match_id": body.match_id,
            "home_team": match.get("home_team"),
            "away_team": match.get("away_team"),
            "kickoff_utc": match.get("kickoff_utc"),
            "outcome": body.outcome.value,
            "stake_usdc": body.stake_usdc,
            "placed_at": datetime.now(timezone.utc),
            "tx_hash": tx_hash,
            "settled": False,
            "payout_usdc": None,
        }
        store.add_prediction(str(prediction_id), record)

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

    all_preds = store.get_predictions()
    user_predictions = [
        PredictionResponse(**p)
        for p in all_preds.values()
        if p["user_address"] == user_address
    ]

    # Sort by most recent first
    user_predictions.sort(key=lambda p: p.placed_at, reverse=True)
    return user_predictions


# ── GET /api/predictions/leaderboard ────────────────────────


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard():
    """Get global prediction leaderboard — includes all predictions (testnet)."""
    all_preds = list(store.get_predictions().values())

    # Include ALL predictions (not just settled) since testnet has no auto-settlement
    user_stats: dict[str, dict] = {}

    for p in all_preds:
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
        if p["settled"] and payout > 0:
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


# ── Shared settlement core ──────────────────────────────
# Used by BOTH the admin endpoint and the background auto-settler.
# Idempotent + reentrancy-safe. No admin-key check — caller is trusted.

def _match_signature(m: dict) -> tuple:
    """Stable identity for a match independent of its id: (home, away, kickoff)."""
    return (m.get("home_team"), m.get("away_team"), m.get("kickoff_utc"))


async def _settle_predictions(
    prediction_ids: list[str], match_id: str, home_score: int, away_score: int
) -> dict:
    """
    Resolve the given prediction ids for a finished match.

    Idempotent: if already settled, returns immediately.
    Reentrancy-safe: per-match asyncio.Lock prevents double-payout.

    Settles regardless of whether the caller matched predictions by id or by
    the (home_team, away_team, kickoff_utc) signature, so positional feed-index
    drift can never strand a bettor.
    """
    if store.is_match_settled(match_id):
        return {
            "status": "already_settled",
            "match_id": match_id,
            "message": "Market already settled. No duplicate action taken.",
        }

    async with _settlement_locks_guard:
        if match_id not in _settlement_locks:
            _settlement_locks[match_id] = asyncio.Lock()

    async with _settlement_locks[match_id]:
        # Double-check after acquiring lock
        if store.is_match_settled(match_id):
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

        # Settle the targeted predictions
        all_preds = store.get_predictions()
        winners = []
        for pid in prediction_ids:
            p = all_preds.get(pid)
            if p is None or p.get("settled"):
                continue
            p["settled"] = True
            if p["outcome"] == actual_outcome:
                p["payout_usdc"] = p["stake_usdc"] * 2
                winners.append(pid)
                # Credit winner's balance with their payout
                try:
                    credit_balance(p["user_address"], p["payout_usdc"])
                    logger.info(
                        "Settlement credit: user=%s, payout=%s USDC, pred=%s",
                        p["user_address"][:12], p["payout_usdc"], pid[:8],
                    )
                except Exception:
                    logger.exception(
                        "Failed to credit winner %s for pred %s",
                        p["user_address"][:12], pid,
                    )
            store.update_prediction(pid, p)

        store.mark_settled(match_id, winners)

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


async def _settle_match_internal(match_id: str, home_score: int, away_score: int) -> dict:
    """Admin path: settle every prediction whose stored match_id == match_id."""
    all_preds = store.get_predictions()
    target = [pid for pid, p in all_preds.items() if p.get("match_id") == match_id]
    return await _settle_predictions(target, match_id, home_score, away_score)


# ── POST /api/predictions/settle (admin) ────────────────

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
    if not ADMIN_SETTLE_KEY:
        logger.error("ADMIN_SETTLE_KEY is not configured — settlement rejected")
        raise HTTPException(
            status_code=401,
            detail="Settlement is not configured on this server (no admin key set)",
        )
    if admin_key != ADMIN_SETTLE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid admin key")

    if home_score is None or away_score is None:
        raise HTTPException(status_code=400, detail="home_score and away_score are required")

    return await _settle_match_internal(match_id, home_score, away_score)


# ── Background auto-settlement ──────────────────────────

async def _auto_settle_finished_matches() -> None:
    """
    Sweep finished matches that have a known full-time score and settle them
    using the football-data feed's score.

    Matches predictions by BOTH the feed match_id AND the stable
    (home_team, away_team, kickoff_utc) signature, so a match whose feed
    position/index drifted between bet-time and now is still settled. Skips
    matches with no score reported yet (waits for the next sweep) and
    already-settled markets.
    """
    matches = await fetch_upcoming_matches()
    all_preds = store.get_predictions()

    for m in matches:
        if m.get("status") != "finished":
            continue
        home_score = m.get("home_score")
        away_score = m.get("away_score")
        if home_score is None or away_score is None:
            # Score not yet reported — wait for the next sweep.
            logger.info(
                "Auto-settle: skipping %s — finished but score not yet reported",
                m.get("match_id"),
            )
            continue

        feed_id = m["match_id"]
        sig = _match_signature(m)
        target: list[str] = []
        for pid, p in all_preds.items():
            if p.get("match_id") == feed_id:
                target.append(pid)
                continue
            p_sig = _match_signature(p)
            if None not in p_sig and p_sig == sig:
                target.append(pid)

        if not target:
            continue
        if store.is_match_settled(feed_id):
            continue
        result = await _settle_predictions(target, feed_id, home_score, away_score)
        logger.info("Auto-settled %s -> %s", feed_id, result.get("status"))


async def start_auto_settle() -> None:
    """Long-running background task that periodically auto-settles finished matches."""
    if not settings.AUTO_SETTLE_ENABLED:
        logger.info("Auto-settlement disabled (AUTO_SETTLE_ENABLED=false)")
        return
    interval = max(10, settings.AUTO_SETTLE_INTERVAL_SECONDS)
    logger.info("Auto-settlement task started (interval=%ss)", interval)
    while True:
        try:
            await _auto_settle_finished_matches()
        except Exception:
            logger.exception("Auto-settlement sweep failed")
        await asyncio.sleep(interval)
