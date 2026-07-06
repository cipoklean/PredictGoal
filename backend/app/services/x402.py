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
}


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
