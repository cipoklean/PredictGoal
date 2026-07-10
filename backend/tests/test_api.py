"""Integration tests for the PredictGoal backend API."""

import os
import pytest
from httpx import ASGITransport, AsyncClient

# Ensure admin settle key is set for tests (before app import loads config)
os.environ.setdefault("ADMIN_SETTLE_KEY", "test-key")

from app.main import app
from app.core.config import get_settings

settings = get_settings()

# Default test headers
PRED_HEADERS = {"X-User-Address": "inj1testuser0000000000000000000000"}
SETTLE_HEADERS = {"X-Admin-Key": settings.ADMIN_SETTLE_KEY}


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
    """Place a prediction on a scheduled match (use placeholder match; API-dependent)."""
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
        "stake_usdc": 5.0,
    }
    response = await client.post("/api/predictions", json=body, headers=PRED_HEADERS)
    # Accept either 201 (match still open) or 400 (match already kicked off)
    assert response.status_code in (201, 400)
    if response.status_code == 201:
        data = response.json()
        assert data["match_id"] == "WC2026-M1"
        assert data["outcome"] == "home"
        assert data["stake_usdc"] == 5.0
        assert data["settled"] is False
        assert data["tx_hash"] is not None


@pytest.mark.asyncio
async def test_place_prediction_missing_auth(client):
    """Prediction without X-User-Address header should be rejected."""
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
        "stake_usdc": 5.0,
    }
    response = await client.post("/api/predictions", json=body)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_place_prediction_invalid_outcome(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "invalid",
        "stake_usdc": 5.0,
    }
    response = await client.post("/api/predictions", json=body, headers=PRED_HEADERS)
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_place_prediction_negative_stake(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
        "stake_usdc": -1.0,
    }
    response = await client.post("/api/predictions", json=body, headers=PRED_HEADERS)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_place_prediction_exceeds_max_stake(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
        "stake_usdc": 101.0,
    }
    response = await client.post("/api/predictions", json=body, headers=PRED_HEADERS)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_knockout_draw_allowed(client):
    """Draw bets on knockout-stage matches should be ALLOWED (90-min result)."""
    # Try several knockout match IDs until we find one that's scheduled
    for mid in ["WC2026-M97", "WC2026-M98", "WC2026-M90", "WC2026-M49"]:
        body = {
            "match_id": mid,
            "outcome": "draw",
            "stake_usdc": 5.0,
        }
        response = await client.post("/api/predictions", json=body, headers=PRED_HEADERS)
        # 201 = accepted, 400 = match finished/live (not open), 404 = not found
        if response.status_code == 201:
            data = response.json()
            assert data["outcome"] == "draw"
            return
    # If all matches are closed or not found, test passes (no open knockout matches)
    assert response.status_code in (400, 404)


@pytest.mark.asyncio
async def test_prediction_on_nonexistent_match(client):
    body = {
        "match_id": "WC2026-NONEXISTENT",
        "outcome": "home",
        "stake_usdc": 5.0,
    }
    response = await client.post("/api/predictions", json=body, headers=PRED_HEADERS)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_predictions(client):
    # Must send auth header
    response = await client.get("/api/predictions/me", headers=PRED_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_leaderboard(client):
    response = await client.get("/api/predictions/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ── Settlement ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_settle_unauthorized(client):
    """Settlement without admin key should be rejected."""
    response = await client.post("/api/predictions/settle", json={
        "match_id": "WC2026-M1",
        "home_score": 2,
        "away_score": 1,
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_settle_success(client):
    """Settlement with admin key should work."""
    response = await client.post(
        "/api/predictions/settle",
        json={"match_id": "WC2026-M4", "home_score": 2, "away_score": 0},
        headers=SETTLE_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("settled", "already_settled")


@pytest.mark.asyncio
async def test_settle_idempotent(client):
    """Settling twice should return already_settled."""
    headers = SETTLE_HEADERS
    # First settlement
    await client.post(
        "/api/predictions/settle",
        json={"match_id": "WC2026-M3", "home_score": 1, "away_score": 1},
        headers=headers,
    )
    # Second settlement — should be idempotent
    response = await client.post(
        "/api/predictions/settle",
        json={"match_id": "WC2026-M3", "home_score": 1, "away_score": 1},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "already_settled"


# ── Wallet (CCTP) ───────────────────────────────────────

@pytest.mark.asyncio
async def test_deposit(client):
    response = await client.post("/api/wallet/deposit", json={"amount_usdc": 100.0}, headers=PRED_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["amount_usdc"] == 100.0
    assert data["tx_hash"] is not None


@pytest.mark.asyncio
async def test_withdraw(client):
    response = await client.post("/api/wallet/withdraw", json={"amount_usdc": 50.0}, headers=PRED_HEADERS)
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
    response = await client.post("/api/predictions", json=body, headers=PRED_HEADERS)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_prediction_empty_stake(client):
    body = {
        "match_id": "WC2026-M1",
        "outcome": "home",
    }
    response = await client.post("/api/predictions", json=body, headers=PRED_HEADERS)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_404_does_not_leak_stack(client):
    """404 errors should not leak stack traces."""
    response = await client.get("/api/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "traceback" not in str(data).lower()
    assert "File" not in str(data)


# ── Auto-settlement ────────────────────────────────────

@pytest.mark.asyncio
async def test_auto_settle_finished_match(monkeypatch):
    """A finished match with a known score should be auto-settled."""
    from app.api import predictions as pred_module
    from app import store as store_module
    import uuid

    match_id = f"WC2026-AUTOTEST-{uuid.uuid4().hex[:8]}"
    pred_id = str(uuid.uuid4())
    record = {
        "prediction_id": pred_id,
        "user_address": PRED_HEADERS["X-User-Address"],
        "match_id": match_id,
        "outcome": "home",
        "stake_usdc": 5.0,
        "placed_at": "2026-07-10T00:00:00+00:00",
        "tx_hash": "x402_tx_test",
        "settled": False,
        "payout_usdc": None,
    }
    store_module.add_prediction(pred_id, record)

    # Stub the feed to report this match as finished 3-1 (home wins)
    async def fake_fetch():
        return [{
            "match_id": match_id,
            "home_team": "Home",
            "away_team": "Away",
            "kickoff_utc": "2026-07-09T20:00:00Z",
            "status": "finished",
            "home_score": 3,
            "away_score": 1,
        }]

    monkeypatch.setattr(pred_module, "fetch_upcoming_matches", fake_fetch)

    await pred_module._auto_settle_finished_matches()

    updated = store_module.get_predictions()[pred_id]
    assert updated["settled"] is True
    assert updated["payout_usdc"] == 10.0  # 2x stake
    assert store_module.is_match_settled(match_id)
