"""Shared in-memory balance store for testnet demo."""

from threading import Lock

_balances: dict[str, float] = {}
_lock = Lock()


def get_balance(user_address: str) -> float:
    """Get a user's testnet balance. Defaults to 100 USDC for new users."""
    return _balances.get(user_address, 100.0)


def credit(user_address: str, amount_usdc: float) -> float:
    """Add to balance. Returns new balance."""
    with _lock:
        current = _balances.get(user_address, 100.0)
        _balances[user_address] = current + amount_usdc
        return _balances[user_address]


def debit(user_address: str, amount_usdc: float) -> float:
    """Deduct from balance. Raises ValueError if insufficient. Returns new balance."""
    with _lock:
        current = _balances.get(user_address, 100.0)
        if current < amount_usdc:
            raise ValueError(
                f"Insufficient balance. You have {current:.1f} USDC, need {amount_usdc:.1f} USDC."
            )
        _balances[user_address] = current - amount_usdc
        return _balances[user_address]
