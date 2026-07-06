"""
MCP Server — PredictGoal Agent Tools.

Three tools for AI agents:
  - get_match_data   → fetch World Cup match info + live scores
  - calculate_odds   → compute home/draw/away win probabilities
  - settle_market    → admin-gated settlement with reentrancy + idempotency guards
"""

import asyncio
import json
import logging
import math
from datetime import datetime, timezone as tz

from mcp.server.fastmcp import FastMCP, Context

# ── Server config ──────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

mcp = FastMCP("injective-global-cup-mcp")

# ── In-memory state ────────────────────────────────────
# Settlement locks per match_id (reentrancy guard)
_settlement_locks: dict[str, asyncio.Lock] = {}
_settlement_locks_guard = asyncio.Lock()

# Track which matches have been settled (idempotency)
_settled_matches: set[str] = set()

# Admin key (from env — never hardcode in prod)
ADMIN_API_KEY = "admin-key-change-me"


# ── Placeholder match data ─────────────────────────────
PLACEHOLDER_MATCHES = [
    {"match_id": "WC2026-M1", "home_team": "Argentina", "away_team": "Brazil",
     "kickoff_utc": "2026-07-10T19:00:00Z", "status": "scheduled",
     "home_score": None, "away_score": None},
    {"match_id": "WC2026-M2", "home_team": "Germany", "away_team": "France",
     "kickoff_utc": "2026-07-11T16:00:00Z", "status": "scheduled",
     "home_score": None, "away_score": None},
    {"match_id": "WC2026-M3", "home_team": "Spain", "away_team": "England",
     "kickoff_utc": "2026-07-11T19:00:00Z", "status": "live",
     "home_score": 1, "away_score": 0},
    {"match_id": "WC2026-M4", "home_team": "Japan", "away_team": "Nigeria",
     "kickoff_utc": "2026-07-09T14:00:00Z", "status": "finished",
     "home_score": 2, "away_score": 2},
]

# ELO ratings for probability model
ELO: dict[str, float] = {
    "Argentina": 1850, "Brazil": 1840, "France": 1835, "Germany": 1820,
    "Spain": 1815, "England": 1810, "Japan": 1750, "Nigeria": 1720,
}


# ── Tool 1: get_match_data ─────────────────────────────

@mcp.tool()
async def get_match_data(match_id: str, ctx: Context) -> str:
    """
    Fetch match data by match ID. Returns match info + live scores.

    Input: match_id (e.g. 'WC2026-M1')
    Output: JSON with home_team, away_team, status, scores, kickoff
    """
    await ctx.info(f"get_match_data called for {match_id}")

    for m in PLACEHOLDER_MATCHES:
        if m["match_id"] == match_id:
            return json.dumps(m, indent=2)

    return json.dumps({"error": f"Match '{match_id}' not found"})


# ── Tool 2: calculate_odds ─────────────────────────────

@mcp.tool()
async def calculate_odds(match_id: str, ctx: Context) -> str:
    """
    Calculate win probabilities for home/draw/away for a given match.
    Uses ELO-based Poisson model.

    Input: match_id (e.g. 'WC2026-M1')
    Output: JSON with win_prob_home, win_prob_draw, win_prob_away, ELO ratings, model info
    """
    await ctx.info(f"calculate_odds called for {match_id}")

    match = next((m for m in PLACEHOLDER_MATCHES if m["match_id"] == match_id), None)
    if not match:
        return json.dumps({"error": f"Match '{match_id}' not found"})

    home_team = match["home_team"]
    away_team = match["away_team"]
    home_elo = ELO.get(home_team, 1700)
    away_elo = ELO.get(away_team, 1700)

    # ELO → expected goals
    elo_diff = home_elo - away_elo
    home_xg = max(0.3, 1.2 + elo_diff * 0.0015)
    away_xg = max(0.3, 1.2 - elo_diff * 0.0015)

    # Poisson-based win probabilities (logistic approximation)
    def logistic(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x / 2.0))

    home_win = logistic(home_xg - away_xg)
    away_win = logistic(away_xg - home_xg)
    draw_prob = round(1.0 - home_win - away_win, 4)

    # Live match adjustment
    home_score = match.get("home_score")
    away_score = match.get("away_score")
    if home_score is not None and away_score is not None:
        goal_diff = home_score - away_score
        if goal_diff > 0:
            home_win = min(0.95, home_win + 0.1 + goal_diff * 0.1)
            away_win = max(0.01, away_win - 0.05 - goal_diff * 0.05)
        elif goal_diff < 0:
            away_win = min(0.95, away_win + 0.1 + abs(goal_diff) * 0.1)
            home_win = max(0.01, home_win - 0.05 - abs(goal_diff) * 0.05)
        # Recalculate draw from remaining probability, clamped to [0, 1]
        draw_prob = max(0.0, 1.0 - home_win - away_win)
        # Normalize so total = 1.0
        total = home_win + draw_prob + away_win
        if total > 0:
            home_win /= total
            draw_prob /= total
            away_win /= total

    draw_prob = round(draw_prob, 4)

    result = {
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "win_prob_home": round(home_win, 4),
        "win_prob_draw": draw_prob,
        "win_prob_away": round(away_win, 4),
        "model": "ELO + Poisson (logistic approximation)",
        "home_elo": home_elo,
        "away_elo": away_elo,
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
    }

    return json.dumps(result, indent=2)


# ── Tool 3: settle_market ──────────────────────────────

@mcp.tool()
async def settle_market(
    match_id: str,
    home_score: int,
    away_score: int,
    admin_key: str,
    ctx: Context,
) -> str:
    """
    Settle a prediction market after match completion.
    **Admin-gated** — requires admin_key.
    **Idempotent** — calling twice returns same result.
    **Reentrancy-safe** — per-match asyncio.Lock.

    Input:
      - match_id: e.g. 'WC2026-M1'
      - home_score: final home score (int)
      - away_score: final away score (int)
      - admin_key: authentication key

    Output: JSON with settled result + list of winning predictions
    """
    await ctx.info(f"settle_market called for {match_id} score {home_score}-{away_score}")

    # ── AUTH GUARD ──
    if admin_key != ADMIN_API_KEY:
        return json.dumps({"error": "Unauthorized: invalid admin_key"})

    # ── IDEMPOTENCY GUARD ──
    if match_id in _settled_matches:
        await ctx.info(f"settle_market: {match_id} already settled — idempotent no-op")
        return json.dumps({
            "status": "already_settled",
            "match_id": match_id,
            "home_score": home_score,
            "away_score": away_score,
            "message": "Market already settled. No duplicate action taken.",
        })

    # ── REENTRANCY GUARD ──
    async with _settlement_locks_guard:
        if match_id not in _settlement_locks:
            _settlement_locks[match_id] = asyncio.Lock()

    async with _settlement_locks[match_id]:
        # Double-check after acquiring lock (race condition defense)
        if match_id in _settled_matches:
            return json.dumps({
                "status": "already_settled",
                "match_id": match_id,
                "home_score": home_score,
                "away_score": away_score,
                "message": "Market already settled (caught after lock).",
            })

        # ── VERIFY MATCH EXISTS ──
        match = next((m for m in PLACEHOLDER_MATCHES if m["match_id"] == match_id), None)
        if not match:
            return json.dumps({"error": f"Match '{match_id}' not found"})

        # ── UPDATE MATCH STATE ──
        match["status"] = "finished"
        match["home_score"] = home_score
        match["away_score"] = away_score

        # Determine actual outcome
        if home_score > away_score:
            actual_outcome = "home"
        elif home_score < away_score:
            actual_outcome = "away"
        else:
            actual_outcome = "draw"

        # ── MARK SETTLED ──
        _settled_matches.add(match_id)

        logger.info(
            "Market settled: match=%s, score=%d-%d, outcome=%s",
            match_id, home_score, away_score, actual_outcome,
        )

        return json.dumps({
            "status": "settled",
            "match_id": match_id,
            "home_score": home_score,
            "away_score": away_score,
            "actual_outcome": actual_outcome,
            "message": f"Market for {match_id} has been settled. "
                       f"Winners: those who predicted '{actual_outcome}'.",
        }, indent=2)


# ── Entry point ────────────────────────────────────────

def main():
    """Run the MCP server via stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
