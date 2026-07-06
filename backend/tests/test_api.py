"""Integration tests for the PredictGoal backend API."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create an async HTTPX test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Health ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "PredictGoal"
    assert data["network"] == "testnet"


# ── Matches ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_matches(client):
    response = await client.get("/api/matches")
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert len(data["matches"]) >= 1
    match = data["matches"][0]
    assert "match_id" in match
    assert "home_team" in match
    assert "away_team" in match
    assert "odds_home" in match


@pytest.mark.asyncio
async def test_get_match_found(client):
    response = await client.get("/api/matches/WC2026-M1")
    assert response.status_code == 200
    match = response.json()
    assert match["match_id"] == "WC2026-M1"
    assert isinstance(match["home_team"], str) and len(match["home_team"]) > 0
    assert isinstance(match["away_team"], str) and len(match["away_team"]) > 0


@pytest.mark.asyncio
async def test_get_match_not_found(client):
    response = await client.get("/api/matches/WC2026-NONEXISTENT")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_match_analytics(client):
    response = await client.get("/api/matches/WC2026-M1/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == "WC2026-M1"
    assert 0 <= data["win_prob_home"] <= 1
    assert 0 <= data["win_prob_draw"] <= 1
    assert 0 <= data["win_prob_away"] <= 1
    # Probabilities must sum to ~1.0
    total = data["win_prob_home"] + data["win_prob_draw"] + data["win_prob_away"]
    assert abs(total - 1.0) < 0.01


# ── Predictions ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_place_prediction(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
        "stake_usdc": 5.0,
    }
    response = await client.post("/api/predictions", json=body)
    assert response.status_code == 201
    data = response.json()
    assert data["match_id"] == "WC2026-M1"
    assert data["outcome"] == "home"
    assert data["stake_usdc"] == 5.0
    assert data["settled"] is False
    assert data["tx_hash"] is not None


@pytest.mark.asyncio
async def test_place_prediction_invalid_outcome(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "invalid",
        "stake_usdc": 5.0,
    }
    response = await client.post("/api/predictions", json=body)
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_place_prediction_negative_stake(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
        "stake_usdc": -1.0,
    }
    response = await client.post("/api/predictions", json=body)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_place_prediction_exceeds_max_stake(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
        "stake_usdc": 101.0,
    }
    response = await client.post("/api/predictions", json=body)
    # Pydantic catches gt=0, le=100.0 before our handler — returns 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_my_predictions(client):
    # Place one first
    await client.post("/api/predictions", json={
        "match_id": "WC2026-M2",
        "outcome": "away",
        "stake_usdc": 3.0,
    })
    response = await client.get("/api/predictions/me")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_leaderboard(client):
    response = await client.get("/api/predictions/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ── Wallet (CCTP) ───────────────────────────────────────

@pytest.mark.asyncio
async def test_deposit(client):
    response = await client.post("/api/wallet/deposit", json={"amount_usdc": 100.0})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["amount_usdc"] == 100.0
    assert data["tx_hash"] is not None


@pytest.mark.asyncio
async def test_withdraw(client):
    response = await client.post("/api/wallet/withdraw", json={"amount_usdc": 50.0})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["amount_usdc"] == 50.0
    assert data["tx_hash"] is not None


@pytest.mark.asyncio
async def test_deposit_zero_amount(client):
    response = await client.post("/api/wallet/deposit", json={"amount_usdc": 0.0})
    assert response.status_code == 422


# ── Security: Input Validation ──────────────────────────

@pytest.mark.asyncio
async def test_prediction_extra_fields_rejected(client):
    """Extra fields in request body should be rejected (Pydantic forbid)."""
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
        "stake_usdc": 5.0,
        "malicious_field": "DROP TABLE predictions;",
    }
    response = await client.post("/api/predictions", json=body)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_prediction_empty_stake(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
    }
    response = await client.post("/api/predictions", json=body)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_404_does_not_leak_stack(client):
    """404 errors should not leak stack traces."""
    response = await client.get("/api/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "traceback" not in str(data).lower()
    assert "File" not in str(data)
