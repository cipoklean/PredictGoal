"""Balance service — thin wrapper over the persistent store.

Existing callers (wallet API, predictions API) import get_balance / credit / debit
from here — these functions now persist to disk via app.store.
"""

from app import store


def get_balance(user_address: str) -> float:
    """Get a user's testnet balance. Defaults to 100 USDC for new users."""
    return store.get_balance(user_address)


def credit(user_address: str, amount_usdc: float) -> float:
    """Add to balance. Returns new balance."""
    return store.credit_balance(user_address, amount_usdc)


def debit(user_address: str, amount_usdc: float) -> float:
    """Deduct from balance. Raises ValueError if insufficient. Returns new balance."""
    return store.debit_balance(user_address, amount_usdc)
