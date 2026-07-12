"""
x402 payment verification — real Injective EVM testnet micropayments.

Uses the x402.org facilitator (free, testnet-only) to verify
payments made in USDC on EVM-compatible chains.

For the hackathon: payments are settled on the Injective EVM testnet
(chain ID 888, eip155:888). Users connect MetaMask with the Injective
EVM testnet network added, so the 2/3 USDC fee is paid "on Injective".
The facilitator is free — no API key needed.
"""

import logging
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# App settings — used only for the APP_ENV production fail-closed check below.
settings = get_settings()

# x402 facilitator URL (free, testnet-only, no API key needed)
X402_FACILITATOR_URL = "https://x402.org/facilitator"

# Endpoint pricing (USDC)
X402_PRICING: dict[str, float] = {
    "/api/predictions": 2.0,
    "/api/insights": 3.0,
    "/api/wallet/withdraw": 0.5,
}

# Payment recipient address (EVM wallet that receives the USDC)
# Set via env: X402_PAYMENT_RECIPIENT = 0x...
X402_PAYMENT_RECIPIENT: str = ""
X402_PROTOCOL_FEE_BPS: int = 50

# Network: Injective EVM testnet (chain ID 888). Users add the Injective EVM
# testnet network to MetaMask and pay the fee there, so predictions are settled
# "on Injective". X402_PAYMENT_RECIPIENT must be an EVM (0x) address on this
# chain — i.e. your Injective EVM address, not the inj1 Cosmos address.
X402_NETWORK = "eip155:888"  # Injective EVM testnet

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

        # Self-test: the x402 SDK only ships 'exact' schemes for known EVM
        # chains. Unknown chains (e.g. Injective EVM eip155:888) raise
        # SchemeNotFoundError when building requirements, so probe it here
        # and fall back to dev-mode passthrough instead of 500-ing per request.
        server.build_payment_requirements(
            ResourceConfig(
                scheme="exact",
                network=X402_NETWORK,
                pay_to=X402_PAYMENT_RECIPIENT,
                price="$0.01",
            )
        )

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

    Enforcement is active ONLY when x402 is configured (X402_PAYMENT_RECIPIENT
    set + SDK present). When x402 is not configured, this is a safe dev-mode
    passthrough (returns True) so local/dev and unconfigured deploys still work.
    """
    required = X402_PRICING.get(path.rstrip("/"), 0.0)
    if required == 0:
        return True  # Free endpoint

    server = get_x402_server()
    if server is None:
        app_env = settings.APP_ENV if settings is not None else "development"
        if app_env == "production":
            # Fail closed in production: never serve paid endpoints unenforced.
            logger.error(
                "x402 not configured in PRODUCTION — refusing %s without payment. "
                "Set X402_PAYMENT_RECIPIENT.", path,
            )
            return False
        # x402 not configured -> dev-mode passthrough (no enforcement)
        logger.warning("x402 not configured — allowing payment for %s in dev mode", path)
        return True

    if payment_header is None:
        logger.warning("x402 payment header missing for %s", path)
        return False  # configured => enforce

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
        logger.warning("x402 payment INVALID for %s: %s", path, result.error or "unknown")
        return False  # configured => enforce

    except Exception as e:
        logger.error("x402 verification error for %s: %s", path, e)
        return False  # configured => enforce (fail closed)


async def build_requirements(path: str) -> Optional[dict]:
    """Return the x402 PaymentRequired v2 ENVELOPE for `path`, or None.

    The JS client (@x402/fetch) parses `X-Payment-Requirements` as a
    PaymentRequired v2 envelope -- i.e. {"x402Version": 2, "accepts": [...],
    "resource": {...}, ...} -- NOT a bare array of requirements. The v2 envelope
    schema also requires a non-null `resource`, so we wrap the built requirements
    via create_payment_required_response (passing a resource) and serialize that,
    rather than dumping the raw list.

    Returns None when x402 is not configured (dev passthrough).
    """
    required = X402_PRICING.get(path.rstrip("/"), 0.0)
    server = get_x402_server()
    if required == 0 or server is None:
        return None
    from x402 import ResourceConfig

    config = ResourceConfig(
        scheme="exact",
        network=X402_NETWORK,
        pay_to=X402_PAYMENT_RECIPIENT,
        price=f"${required:.2f}",
    )
    try:
        reqs = server.build_payment_requirements(config)
        # The v2 envelope schema the JS client (@x402/fetch) parses via its
        # PaymentRequiredSchema requires a non-null `resource`. The Python SDK
        # serializes every optional field as explicit `null` (e.g. error:null,
        # resource.mimeType:null). zod's `.optional()` accepts a MISSING
        # field but REJECTS explicit `null`, so those would fail client-side
        # parsing. We strip all nulls so optional fields are simply absent.
        # create_payment_required_response is async on x402ResourceServer.
        envelope = await server.create_payment_required_response(
            reqs,
            resource={"url": path},
        )
    except Exception as e:
        logger.error("x402 build_requirements failed for %s: %s", path, e)
        return None
    return _strip_nulls(envelope.model_dump(mode="json"))


def _strip_nulls(obj):
    """Recursively drop explicit ``None`` values so zod `.optional()` fields
    (which reject ``null`` but accept a missing key) parse cleanly."""
    if isinstance(obj, dict):
        return {k: _strip_nulls(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, (list, tuple)):
        return [_strip_nulls(v) for v in obj if v is not None]
    return obj


def load_config(payment_recipient: str):
    """Load x402 config from env — call once at startup."""
    global X402_PAYMENT_RECIPIENT
    X402_PAYMENT_RECIPIENT = payment_recipient.strip()
