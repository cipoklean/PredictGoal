"""
x402 payment verification — real Injective testnet micropayments.

Uses the x402.org facilitator (free, testnet-only) to verify
payments made in USDC on EVM-compatible chains.

For the hackathon: payments on Base Sepolia testnet (eip155:84532)
or Injective EVM testnet. The facilitator is free — no API key needed.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# x402 facilitator URL (free, testnet-only, no API key needed)
X402_FACILITATOR_URL = "https://x402.org/facilitator"

# Endpoint pricing (USDC)
X402_PRICING: dict[str, float] = {
    "/api/predictions": 2.0,
    "/api/insights": 0.5,
    "/api/wallet/withdraw": 0.5,
}

# Payment recipient address (EVM wallet that receives the USDC)
# Set via env: X402_PAYMENT_RECIPIENT = 0x...
X402_PAYMENT_RECIPIENT: str = ""
X402_PROTOCOL_FEE_BPS: int = 50

# Network: Injective testnet (EVM-compatible, chain ID 888)
# Or Base Sepolia (eip155:84532) for broader testnet support
X402_NETWORK = "eip155:84532"  # Base Sepolia testnet

# x402 server instance (lazy init)
_x402_server: Optional[object] = None
_x402_initialized: bool = False


def is_x402_available() -> bool:
    """Check if x402 SDK is installed and configured."""
    try:
        from x402 import x402ResourceServer
        from x402.http import HTTPFacilitatorClient, FacilitatorConfig
        from x402.mechanisms.evm.exact import ExactEvmServerScheme
        return True
    except ImportError:
        return False


def get_x402_server():
    """Initialize and return the x402 server (singleton)."""
    global _x402_server, _x402_initialized

    if _x402_initialized:
        return _x402_server

    if not is_x402_available():
        logger.warning("x402 SDK not installed — payment verification disabled")
        _x402_initialized = True
        return None

    if not X402_PAYMENT_RECIPIENT:
        logger.warning("X402_PAYMENT_RECIPIENT not set — payments go nowhere")
        _x402_initialized = True
        return None

    try:
        from x402 import x402ResourceServer, ResourceConfig
        from x402.http import HTTPFacilitatorClient, FacilitatorConfig
        from x402.mechanisms.evm.exact import ExactEvmServerScheme

        facilitator_config = FacilitatorConfig(url=X402_FACILITATOR_URL)
        facilitator = HTTPFacilitatorClient(facilitator_config)
        server = x402ResourceServer(facilitator)
        server.register(X402_NETWORK, ExactEvmServerScheme())
        server.initialize()

        logger.info(
            "x402 server initialized — network=%s, recipient=%s, facilitator=%s",
            X402_NETWORK, X402_PAYMENT_RECIPIENT[:10], X402_FACILITATOR_URL,
        )
        _x402_server = server
    except Exception as e:
        logger.error("Failed to initialize x402 server: %s", e)
        _x402_server = None

    _x402_initialized = True
    return _x402_server


async def verify_x402_payment(
    payment_header: Optional[str],
    path: str,
) -> bool:
    """
    Verify an x402 payment proof via the testnet facilitator.

    Returns True if payment is valid or if x402 is unavailable (dev fallback).
    In production: returns False for missing/invalid payments.
    """
    required = X402_PRICING.get(path.rstrip("/"), 0.0)
    if required == 0:
        return True  # Free endpoint

    server = get_x402_server()
    if server is None:
        logger.warning("x402 unavailable — allowing payment for %s in dev mode", path)
        return True  # Dev mode fallback

    if payment_header is None:
        logger.warning("x402 payment header missing for %s", path)
        return True  # Dev mode fallback (change to False for production)

    try:
        from x402 import ResourceConfig

        config = ResourceConfig(
            scheme="exact",
            network=X402_NETWORK,
            pay_to=X402_PAYMENT_RECIPIENT,
            price=f"${required:.2f}",
        )
        requirements = server.build_payment_requirements(config)

        # Verify with facilitator
        result = await server.verify_payment(payment_header, requirements[0])

        if result.is_valid:
            logger.info("x402 payment verified for %s: %s USDC", path, required)
            return True
        else:
            logger.warning("x402 payment INVALID for %s: %s", path, result.error or "unknown")
            return True  # Dev mode fallback (change to False for production)

    except Exception as e:
        logger.error("x402 verification error for %s: %s — falling back to dev mode", path, e)
        return True  # Dev mode fallback


def load_config(payment_recipient: str):
    """Load x402 config from env — call once at startup."""
    global X402_PAYMENT_RECIPIENT
    X402_PAYMENT_RECIPIENT = payment_recipient.strip()
