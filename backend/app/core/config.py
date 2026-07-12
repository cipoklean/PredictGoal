from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "PredictGoal"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Injective Testnet
    INJECTIVE_NETWORK: str = "testnet"
    INJECTIVE_RPC_URL: str = "https://testnet.sentry.tm.injective.network:443"
    INJECTIVE_CHAIN_ID: str = "injective-888"
    INJECTIVE_GRPC_URL: str = "testnet.grpc.injective.network:443"
    INJECTIVE_MNEMONIC: str = ""

    # CCTP Testnet
    CCTP_API_KEY: str = ""
    CCTP_SOURCE_DOMAIN: int = 0
    CCTP_TOKEN_MESSENGER_ADDRESS: str = ""

    # x402
    X402_PAYMENT_RECIPIENT: str = ""
    X402_PROTOCOL_FEE_BPS: int = 50
    # x402 enforcement mode.
    #   "passthrough" (default): serve paid endpoints WITHOUT requiring payment.
    #       Used for the hackathon demo on the Injective EVM testnet (chain 1439)
    #       where no hosted x402 facilitator exists -- the 402 flow is fully
    #       wired but not enforced, so zero real funds move.
    #   "enforce": require a valid x402 payment proof (needs a working
    #       facilitator + supported chain). Fail-closed if x402 cannot init.
    X402_MODE: str = "passthrough"

    # Admin — required for settlement. No default (must be set in env).
    ADMIN_SETTLE_KEY: str = ""

    # Auto-settlement — resolves finished matches using the football-data score.
    # When enabled, a background task sweeps matches the feed reports as
    # FINISHED (with a known full-time score) and settles them automatically.
    AUTO_SETTLE_ENABLED: bool = True
    AUTO_SETTLE_INTERVAL_SECONDS: int = 60

    # Store path — where the JSON store is written.
    # On Render this points at the mounted persistent disk (/data/store.json).
    # If unset, defaults to backend/data/store.json (local dev, gitignored).
    STORE_PATH: str | None = None

    # World Cup Data
    FOOTBALL_DATA_API_KEY: str = ""
    FOOTBALL_DATA_COMPETITION_CODE: str = "WC"

    # CORS — comma-separated origins
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Monitoring — set to false to disable /health endpoint
    HEALTH_CHECK_ENABLED: bool = True

    # Redis (optional — not used by MVP)
    REDIS_URL: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
