# PredictGoal MCP Server

Standalone Model Context Protocol server that AI agents (Claude Desktop, Cursor, Hermes) can connect to for World Cup match analytics and market settlement.

## Quick Start

```bash
cd mcp-server
uv sync
uv run python server.py
```

The server runs over **stdio** transport — it's designed to be called by AI agents, not humans.

## Connecting to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "predictgoal": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/absolute/path/to/mcp-server"
    }
  }
}
```

Restart Claude Desktop. The three tools will appear automatically.

## Connecting to Cursor

In Cursor settings → MCP Servers, add:

- **Name:** PredictGoal
- **Command:** `uv run python server.py`
- **Working Directory:** `/absolute/path/to/mcp-server`

## Available Tools

### 1. `get_match_data`
Fetch World Cup match info by ID.

```
Input:  {"match_id": "WC2026-M1"}
Output: {"match_id": "WC2026-M1", "home_team": "Argentina", "away_team": "Brazil", ...}
```

### 2. `calculate_odds`
Compute ELO + Poisson win probabilities.

```
Input:  {"match_id": "WC2026-M1"}
Output: {"match_id": "WC2026-M1", "win_prob_home": 0.504, "win_prob_draw": 0.235, ...}
```

### 3. `settle_market`
Admin-only settlement with reentrancy + idempotency guards.

```
Input:  {"match_id": "WC2026-M1", "home_score": 2, "away_score": 1, "admin_key": "..."}
Output: {"status": "settled", "match_id": "WC2026-M1", "actual_outcome": "home", ...}
```

**Security:**
- Requires `admin_key` matching `ADMIN_API_KEY` in the server
- Idempotent: calling twice on the same match returns `"already_settled"`
- Reentrancy-safe: per-match `asyncio.Lock` prevents concurrent double-settlement

## Demo Script

Use this demo flow in your video:

```
1. Open Claude Desktop or Cursor
2. Ask: "What are the odds for WC2026-M3?"
   → Agent calls calculate_odds → gets Spain 61% / Draw 18% / England 21%
3. Ask: "Settle WC2026-M1 with score 2-1 Argentina wins"
   → Agent calls settle_market with admin_key
   → Returns settled status with winning predictions
4. Ask: "Settle WC2026-M1 again"
   → Returns "already_settled" — idempotent
```

## Limitations (for judging)

- **Match data:** Uses a hardcoded placeholder dataset (4 matches). In production, fetches from football-data.org via the backend API.
- **Settlement:** Updates in-memory state only. No on-chain settlement or payout mechanism in the MCP server (that's handled by the backend).
- **Transport:** stdio only. For HTTP/SSE transport, use the FastAPI backend's `/api/predictions/settle` endpoint.
