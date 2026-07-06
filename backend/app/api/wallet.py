"""Wallet API endpoints — CCTP deposit/withdraw and balance for testnet USDC."""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.services.cctp import deposit_usdc, withdraw_usdc, CCTPTransferResult
from app.services.balance import get_balance, credit as credit_balance, debit as debit_balance

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/wallet", tags=["wallet"])


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
    """Deposit USDC from source chain to Injective testnet via CCTP. Testnet only."""
    user_address = request.headers.get("X-User-Address", "inj1testuser0000000000000000000000")
    if not user_address:
        raise HTTPException(status_code=401, detail="X-User-Address header required")

    result = await deposit_usdc(
        user_address=user_address, amount_usdc=body.amount_usdc, source_domain=body.source_domain,
    )
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error or "CCTP deposit failed")

    credit_balance(user_address, body.amount_usdc)
    logger.info("Deposit: user=%s, amount=%s USDC", user_address, body.amount_usdc)
    return TransferResponse(success=True, tx_hash=result.tx_hash, amount_usdc=body.amount_usdc)


@router.post("/withdraw", response_model=TransferResponse, status_code=status.HTTP_200_OK)
async def withdraw(request: Request, body: WithdrawRequest):
    """Withdraw USDC from Injective testnet back to source chain via CCTP. Testnet only."""
    user_address = request.headers.get("X-User-Address", "inj1testuser0000000000000000000000")
    if not user_address:
        raise HTTPException(status_code=401, detail="X-User-Address header required")

    try:
        debit_balance(user_address, body.amount_usdc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await withdraw_usdc(
        user_address=user_address, amount_usdc=body.amount_usdc, destination_domain=body.destination_domain,
    )
    if not result.success:
        credit_balance(user_address, body.amount_usdc)  # rollback
        raise HTTPException(status_code=502, detail=result.error or "CCTP withdraw failed")

    logger.info("Withdraw: user=%s, amount=%s USDC", user_address, body.amount_usdc)
    return TransferResponse(success=True, tx_hash=result.tx_hash, amount_usdc=body.amount_usdc)


# ── Balance ──────────────────────────────────────────────

class BalanceResponse(BaseModel):
    user_address: str
    balance_usdc: float


@router.get("/balance", response_model=BalanceResponse)
async def get_balance_endpoint(request: Request):
    """Get the testnet USDC balance for the connected wallet."""
    user_address = (request.headers.get("X-User-Address") or "").strip()
    if not user_address:
        raise HTTPException(status_code=401, detail="X-User-Address header required")
    return BalanceResponse(user_address=user_address, balance_usdc=get_balance(user_address))
