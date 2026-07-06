"""CCTP (Cross-Chain Transfer Protocol) service stub.

Handles USDC deposits/withdrawals via Circle's CCTP across Injective testnet.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CCTPTransferResult:
    success: bool
    tx_hash: str | None = None
    error: str | None = None
    amount_usdc: float = 0.0


async def deposit_usdc(
    user_address: str,
    amount_usdc: float,
    source_domain: int = 0,  # Ethereum Sepolia default
) -> CCTPTransferResult:
    """
    Deposit USDC from source chain to Injective testnet via CCTP.

    In production, this calls Circle's CCTP API:
    1. Approve USDC spend on source chain
    2. Call depositForBurn on TokenMessenger
    3. Wait for attestation from Circle
    4. Call receiveMessage on destination chain

    Stub: always succeeds on testnet.
    """
    logger.info(
        "CCTP deposit: user=%s, amount=%s USDC, domain=%s",
        user_address, amount_usdc, source_domain,
    )
    return CCTPTransferResult(
        success=True,
        tx_hash=f"cctp_deposit_{user_address[:8]}_{amount_usdc}",
        amount_usdc=amount_usdc,
    )


async def withdraw_usdc(
    user_address: str,
    amount_usdc: float,
    destination_domain: int = 0,
) -> CCTPTransferResult:
    """
    Withdraw USDC from Injective testnet back to source chain via CCTP.

    Stub: always succeeds on testnet.
    """
    logger.info(
        "CCTP withdraw: user=%s, amount=%s USDC, dest_domain=%s",
        user_address, amount_usdc, destination_domain,
    )
    return CCTPTransferResult(
        success=True,
        tx_hash=f"cctp_withdraw_{user_address[:8]}_{amount_usdc}",
        amount_usdc=amount_usdc,
    )
