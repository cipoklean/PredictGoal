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

    # Admin — required for settlement. No default (must be set in env).
    ADMIN_SETTLE_KEY: str = ""

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
