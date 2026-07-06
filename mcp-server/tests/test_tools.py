"""Tests for the MCP server tools."""

import json
import sys
import pytest

sys.path.insert(0, ".")
from server import get_match_data, calculate_odds, settle_market, ADMIN_API_KEY


class MockCtx:
    """Mock MCP Context for testing tools."""
    async def info(self, msg: str) -> None:
        pass


@pytest.fixture
def ctx():
    return MockCtx()


@pytest.mark.asyncio
async def test_get_match_data_found(ctx):
    result = await get_match_data("WC2026-M1", ctx)
    data = json.loads(result)
    assert data["match_id"] == "WC2026-M1"
    assert data["home_team"] == "Argentina"
    assert data["away_team"] == "Brazil"


@pytest.mark.asyncio
async def test_get_match_data_not_found(ctx):
    result = await get_match_data("NONEXISTENT", ctx)
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_calculate_odds(ctx):
    result = await calculate_odds("WC2026-M1", ctx)
    data = json.loads(result)
    assert data["match_id"] == "WC2026-M1"
    assert 0 <= data["win_prob_home"] <= 1
    assert 0 <= data["win_prob_draw"] <= 1
    assert 0 <= data["win_prob_away"] <= 1
    total = data["win_prob_home"] + data["win_prob_draw"] + data["win_prob_away"]
    assert abs(total - 1.0) < 0.01


@pytest.mark.asyncio
async def test_settle_market_unauthorized(ctx):
    result = await settle_market("WC2026-M4", 2, 2, "wrong-key", ctx)
    assert "Unauthorized" in result


@pytest.mark.asyncio
async def test_settle_market_success(ctx):
    result = await settle_market("WC2026-M3", 3, 1, ADMIN_API_KEY, ctx)
    data = json.loads(result)
    assert data["status"] == "settled"
    assert data["actual_outcome"] == "home"


@pytest.mark.asyncio
async def test_settle_market_idempotent(ctx):
    # First settlement
    await settle_market("WC2026-M2", 1, 1, ADMIN_API_KEY, ctx)
    # Second — should be idempotent
    result = await settle_market("WC2026-M2", 1, 1, ADMIN_API_KEY, ctx)
    data = json.loads(result)
    assert data["status"] == "already_settled"
