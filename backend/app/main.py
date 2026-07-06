"""FastAPI application entry point for PredictGoal backend."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.matches import router as matches_router
from app.api.predictions import router as predictions_router
from app.api.wallet import router as wallet_router
from app.core.config import get_settings

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PredictGoal — Prediction Market API",
    description=(
        "Non-custodial World Cup 2026 prediction market. "
        "Built with Injective x402, CCTP, MCP Server, and Agent Skills. "
        "Testnet only — no real funds."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (TODO: enable via slowapi)
# from slowapi import Limiter, _rate_limit_exceeded_handler
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Register routers
app.include_router(matches_router)
app.include_router(predictions_router)
app.include_router(wallet_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "network": settings.INJECTIVE_NETWORK,
        "chain_id": settings.INJECTIVE_CHAIN_ID,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler — never leak stack traces."""
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs."},
    )
