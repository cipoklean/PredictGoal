"""
Persistent JSON-file-backed store for balances and predictions.

Survives server restarts (Render free tier keeps disk within same deploy).
Thread-safe via per-key locks.

Data layout on disk (data/store.json):
{
  "balances": {"0xabc...": 95.5, "inj1xyz...": 100.0},
  "predictions": {
    "uuid-1": {"prediction_id": "...", "user_address": "...", ...},
    "uuid-2": {...}
  },
  "settled_matches": ["match-1", "match-2"]
}
"""

import json
import logging
import os
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "store.json"

# In-memory cache (loaded once at startup, saved on every mutation)
_balances: dict[str, float] = {}
_predictions: dict[str, dict] = {}
_settled_matches: set[str] = set()

_store_path: Path = DEFAULT_STORE_PATH
_write_lock = Lock()
_balance_lock = Lock()  # protects _balances read-modify-write
_loaded = False


def _ensure_dir() -> None:
    """Create the data directory if it doesn't exist."""
    _store_path.parent.mkdir(parents=True, exist_ok=True)


def init(store_path: str | None = None) -> None:
    """
    Load persisted data from disk (or initialize empty state).
    Must be called once at startup before any reads.
    """
    global _store_path, _loaded, _balances, _predictions, _settled_matches

    if _loaded:
        logger.warning("Store already initialized — skipping re-init")
        return

    if store_path:
        _store_path = Path(store_path)
    _ensure_dir()

    if _store_path.exists():
        try:
            with open(_store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _balances = data.get("balances", {})
            _predictions = data.get("predictions", {})
            _settled_matches = set(data.get("settled_matches", []))
            logger.info(
                "Loaded store: %d balances, %d predictions, %d settled matches",
                len(_balances), len(_predictions), len(_settled_matches),
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load store.json, starting fresh: %s", e)
            _balances = {}
            _predictions = {}
            _settled_matches = set()
    else:
        logger.info("No existing store.json found — starting fresh")
        _balances = {}
        _predictions = {}
        _settled_matches = set()

    _loaded = True


def _save() -> None:
    """Persist current state to disk. Thread-safe."""
    global _balances, _predictions, _settled_matches
    with _write_lock:
        _ensure_dir()
        data = {
            "balances": _balances,
            "predictions": _predictions,
            "settled_matches": sorted(_settled_matches),
        }
        # Atomic write: write to temp file, then rename
        tmp_path = _store_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            os.replace(tmp_path, _store_path)
        except OSError as e:
            logger.error("Failed to persist store: %s", e)
            raise


# ── Balance operations ────────────────────────────────


def get_balance(user_address: str) -> float:
    """Get a user's testnet balance. Defaults to 100 USDC for new users."""
    if not _loaded:
        raise RuntimeError("Store not initialized — call store.init() at startup")
    return _balances.get(user_address, 100.0)


def credit_balance(user_address: str, amount_usdc: float) -> float:
    """Add to a user's balance. Returns new balance. Thread-safe."""
    if not _loaded:
        raise RuntimeError("Store not initialized")
    with _balance_lock:
        current = _balances.get(user_address, 100.0)
        _balances[user_address] = current + amount_usdc
        _save()
        return _balances[user_address]


def debit_balance(user_address: str, amount_usdc: float) -> float:
    """Deduct from a user's balance. Raises ValueError if insufficient. Thread-safe."""
    if not _loaded:
        raise RuntimeError("Store not initialized")
    with _balance_lock:
        current = _balances.get(user_address, 100.0)
        if current < amount_usdc:
            raise ValueError(
                f"Insufficient balance. You have {current:.1f} USDC, "
                f"need {amount_usdc:.1f} USDC."
            )
        _balances[user_address] = current - amount_usdc
        _save()
        return _balances[user_address]


# ── Prediction operations ─────────────────────────────


def get_predictions() -> dict[str, dict]:
    """Get all predictions (returns a copy to avoid mutation outside store)."""
    if not _loaded:
        raise RuntimeError("Store not initialized")
    return dict(_predictions)


def add_prediction(prediction_id: str, record: dict) -> None:
    """Add a new prediction."""
    if not _loaded:
        raise RuntimeError("Store not initialized")
    _predictions[prediction_id] = record
    _save()


def update_prediction(prediction_id: str, updates: dict) -> None:
    """Update fields on an existing prediction (e.g., settle it)."""
    if not _loaded:
        raise RuntimeError("Store not initialized")
    if prediction_id in _predictions:
        _predictions[prediction_id].update(updates)
        _save()


def mark_settled(match_id: str, winners: list[str]) -> None:
    """
    Batch-settle all predictions for a match.
    Returns nothing — caller is responsible for computing payouts.
    """
    if not _loaded:
        raise RuntimeError("Store not initialized")
    _settled_matches.add(match_id)
    _save()


def is_match_settled(match_id: str) -> bool:
    """Check if a match has already been settled."""
    if not _loaded:
        raise RuntimeError("Store not initialized")
    return match_id in _settled_matches
