"""Wallet API endpoints — CCTP deposit/withdraw and balance for testnet USDC."""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.services.cctp import deposit_usdc, withdraw_usdc, CCTPTransferResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/wallet", tags=["wallet"])

# In-memory balance store (testnet only — lost on restart)
_user_balances: dict[str, float] = {}


def _get_balance(user_address: str) -> float:
    """Get simulated testnet balance for a user."""
    return _user_balances.get(user_address, 100.0)  # Default: 100 USDC testnet


class DepositRequest(BaseModel):
    amount_usdc: float = Field(..., gt=0, le=10000, description="Amount in USDC to deposit")
    source_domain: int = Field(default=0, description="Source chain domain (0=Ethereum Sepolia)")

    model_config = {"extra": "forbid"}


class WithdrawRequest(BaseModel):
    amount_usdc: float = Field(..., gt=0, le=10000, description="Amount in USDC to withdraw")
    destination_domain: int = Field(default=0, description="Destination chain domain (0=Ethereum Sepolia)")

    model_config = {"extra": "forbid"}


class TransferResponse(BaseModel):
    success: bool
    tx_hash: str | None = None
    error: str | None = None
    amount_usdc: float


@router.post("/deposit", response_model=TransferResponse, status_code=status.HTTP_200_OK)
async def deposit(request: Request, body: DepositRequest):
    """
    Deposit USDC from source chain to Injective testnet via CCTP.

    Testnet only — no real funds involved.
    """
    user_address = request.headers.get("X-User-Address", "inj1testuser0000000000000000000000")

    if not user_address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Address header required",
        )

    result = await deposit_usdc(
        user_address=user_address,
        amount_usdc=body.amount_usdc,
        source_domain=body.source_domain,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.error or "CCTP deposit failed",
        )

    # Update simulated balance
    _user_balances[user_address] = _get_balance(user_address) + body.amount_usdc

    logger.info("Deposit successful: user=%s, amount=%s USDC, new_balance=%s",
                user_address, body.amount_usdc, _user_balances[user_address])
    return TransferResponse(
        success=True,
        tx_hash=result.tx_hash,
        amount_usdc=body.amount_usdc,
    )


@router.post("/withdraw", response_model=TransferResponse, status_code=status.HTTP_200_OK)
async def withdraw(request: Request, body: WithdrawRequest):
    """
    Withdraw USDC from Injective testnet back to source chain via CCTP.

    Testnet only — no real funds involved.
    """
    user_address = request.headers.get("X-User-Address", "inj1testuser0000000000000000000000")

    if not user_address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Address header required",
        )

    result = await withdraw_usdc(
        user_address=user_address,
        amount_usdc=body.amount_usdc,
        destination_domain=body.destination_domain,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.error or "CCTP withdraw failed",
        )

    # Deduct from simulated balance
    current = _get_balance(user_address)
    if current < body.amount_usdc:
        raise HTTPException(status_code=400, detail="Insufficient testnet balance")
    _user_balances[user_address] = current - body.amount_usdc

    logger.info("Withdraw successful: user=%s, amount=%s USDC, new_balance=%s",
                user_address, body.amount_usdc, _user_balances[user_address])
    return TransferResponse(
        success=True,
        tx_hash=result.tx_hash,
        amount_usdc=body.amount_usdc,
    )


# ── Balance ──────────────────────────────────────────────

class BalanceResponse(BaseModel):
    user_address: str
    balance_usdc: float


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(request: Request):
    """Get the testnet USDC balance for the connected wallet."""
    user_address = (request.headers.get("X-User-Address") or "").strip()
    if not user_address:
        raise HTTPException(status_code=401, detail="X-User-Address header required")
    return BalanceResponse(
        user_address=user_address,
        balance_usdc=_get_balance(user_address),
    )
