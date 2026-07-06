"""x402 middleware — Injective pay-per-use protocol integration (stub)."""

import logging
from typing import Callable

from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

# Map of endpoint paths to required USDC amount (in wei-equivalent, using 6 decimals)
X402_PRICING: dict[str, float] = {
    "/api/predictions": 0.1,   # 0.1 USDC per prediction
    "/api/deposit": 0.0,        # free (user brings their own funds)
    "/api/withdraw": 0.5,       # 0.5 USDC withdrawal fee
    "/api/insights": 0.5,       # 0.5 USDC per premium insight
}


async def verify_x402_payment(payment_header: str | None, path: str) -> bool:
    """
    Verify an x402 payment proof on Injective testnet.

    In production, this would:
    1. Parse the payment proof from the header
    2. Call the Injective facilitator to verify on-chain
    3. Check amount >= required price for the endpoint
    4. Check the receipt hasn't been replayed (nonce/idempotency)

    Returns True if payment is valid, False otherwise.

    STUB: always returns True in dev mode.
    """
    required = X402_PRICING.get(path.rstrip("/"), 0.0)
    if required == 0:
        return True  # Free endpoint

    if payment_header is None:
        logger.warning("x402 payment missing for %s — allowing in dev mode", path)
        return True  # In production: return False

    # TODO: Real verification via Injective facilitator
    logger.info("x402 payment header present for %s: %s...", path, payment_header[:20])
    return True


async def x402_middleware(request: Request, call_next: Callable) -> dict:
    """
    Injective x402 middleware stub.

    In production, this would:
    1. Extract x402 payment proof from request headers
    2. Verify the proof on Injective chain
    3. Check amount >= required price for the endpoint
    4. Forward or reject

    For now, all requests pass through with a warning.
    """
    path = request.url.path.rstrip("/")
    required_amount = X402_PRICING.get(path, 0.0)

    if required_amount > 0:
        payment_header = request.headers.get("X-402-Payment")
        if payment_header is None:
            logger.warning(
                "x402 payment missing for %s (required: %s USDC) — passing in dev mode",
                path, required_amount,
            )
            # In production: raise HTTPException(status_code=402, detail="Payment required")
        else:
            logger.info("x402 payment received for %s: %s", path, payment_header[:20])

    response = await call_next(request)
    return response
