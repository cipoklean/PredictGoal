# ⚽ PredictGoal — Prediction Market + AI Analytics

**Hackathon:** The Injective Global Cup (Jul 3–19, 2026)
**Built with:** x402, CCTP, MCP Server, Agent Skills

A non-custodial, micro-stakes prediction market for World Cup matches with real-time AI-powered win probabilities — built on Injective's newest technologies. **Testnet only. Zero real funds.**

---

## What it does

World Cup fans can:
- Browse live and upcoming World Cup 2026 matches
- View **AI-generated win probabilities** for Home/Draw/Away outcomes
- Place micro-stake predictions (as low as 0.1 USDC) via **Injective x402** pay-per-use
- Deposit and withdraw testnet USDC via **Circle's CCTP** cross-chain bridge
- Track their predictions and compete on a global **leaderboard**
- Markets are **auto-settled** post-match by an **MCP Server agent** with reentrancy + idempotency guards

---

## How Injective Technologies Are Used

### 🔐 x402 — Pay-per-Use Prediction

Every prediction placement (`POST /api/predictions`) requires an **x402 payment proof** header. The backend validates the payment on Injective testnet before accepting the prediction. This enables a **decentralized micropayment model** where users pay per prediction with no subscription or custody.

**Implementation:** `backend/app/services/x402.py` — middleware intercepts requests, verifies x402 header, and enforces per-endpoint pricing (0.1 USDC/prediction, 0.5 USDC/withdrawal).

### 🌉 CCTP — Cross-Chain USDC Transfers

Users can **deposit USDC from Ethereum Sepolia to Injective testnet** and **withdraw back** using Circle's Cross-Chain Transfer Protocol. This enables a seamless multi-chain experience where users bring USDC from any supported chain.

**Implementation:** `backend/app/services/cctp.py` — stubs for `depositForBurn` and `receiveMessage` flows via Circle's testnet API. `backend/app/api/wallet.py` — REST endpoints for deposit/withdraw.

### 🤖 MCP Server — Agent Tools for Analytics & Settlement

A standalone **Model Context Protocol server** exposes three tools that AI agents can call:

| Tool | Description |
|------|-------------|
| `get_match_data` | Fetch match info + live scores from World Cup data |
| `calculate_odds` | ELO + Poisson-based win probability model |
| `settle_market` | Admin-gated settlement with **reentrancy lock + idempotency** |

**Implementation:** `mcp-server/server.py` — FastMCP server with three registered tools. The settlement tool uses `asyncio.Lock` per match for reentrancy safety and a `_settled_matches` set for idempotency.

### 🧠 Agent Skills — AI-Powered Analytics

The `calculate_odds` tool implements an **ELO + Poisson probability model** that:
- Computes expected goals from team ELO ratings
- Converts to win/draw/loss probabilities via logistic approximation
- Adjusts in real-time for live scores
- Surfaces key stats (ELO, xG, model name)

This is exposed to AI agents via the MCP server, enabling agent-driven analytics and settlement.

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌───────────────┐
│  React/Vite  │────▶│   FastAPI    │────▶│  Injective     │
│  Frontend    │     │   Backend    │     │  Testnet       │
│              │     │              │     │  (x402, CCTP)  │
│ - Matches    │     │ - x402 mw   │     └───────────────┘
│ - Predict UI │     │ - CCTP svc  │
│ - Analytics  │     │ - MCP client│
│ - Leaderboard│     └──────┬───────┘
└──────────────┘            │
                            ▼
                    ┌──────────────┐
                    │  MCP Server  │
                    │  (Agent      │
                    │   Skills)    │
                    │              │
                    │ - match data │
                    │ - odds calc  │
                    │ - settlement │
                    └──────────────┘
```

---

## Is Injective Integrated?

**Yes** — the project integrates with Injective testnet via:
- **x402** payment protocol for per-prediction micropayments
- **CCTP** for cross-chain USDC bridging to/from Injective
- Designed to work with Injective WASM smart contracts (stretch goal for escrow logic)

The backend is configured for `injective-888` testnet with Injective RPC/gRPC endpoints.

---

## Quick Start

### Prerequisites
- Python 3.11+ with `uv`
- Node.js 20+

### Backend
```bash
cd backend
cp .env.example .env
# Edit .env with your FOOTBALL_DATA_API_KEY (or leave blank for placeholder data)
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### MCP Server
```bash
cd mcp-server
uv sync
uv run python server.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Run all tests
```bash
cd backend && uv run pytest tests/ -v    # 17 tests
cd mcp-server && uv run pytest tests/ -v  # 6 tests
```

---

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/matches` | List all World Cup matches | — |
| GET | `/api/matches/{id}` | Match detail + odds | — |
| GET | `/api/matches/{id}/analytics` | AI win probabilities | — |
| POST | `/api/predictions` | Place prediction | x402 |
| GET | `/api/predictions/me` | My predictions | Wallet addr |
| GET | `/api/predictions/leaderboard` | Global leaderboard | — |
| POST | `/api/wallet/deposit` | CCTP deposit USDC | Wallet addr |
| POST | `/api/wallet/withdraw` | CCTP withdraw USDC | Wallet addr |
| GET | `/health` | Health check | — |

---

## Security

- **Input validation** — Pydantic models with strict enums, Decimal for money, `extra=forbid`
- **No stack traces to clients** — global exception handler
- **Extra fields rejected** — Pydantic `extra=forbid` prevents injection
- **Admin-only settlement** — MCP server checks `admin_key` before settling
- **Reentrancy guard** — `asyncio.Lock` per `match_id`
- **Idempotent settlement** — duplicate calls return "already_settled"
- **No private keys in repo** — all secrets via `.env`

---

## Project Structure

```
predictgoal/
├── SPEC.md                 # Design spec
├── README.md               # This file
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── app/
│   │   ├── main.py         # FastAPI entry point
│   │   ├── core/config.py  # Settings from env
│   │   ├── api/            # Routers (matches, predictions, wallet)
│   │   ├── services/       # Business logic (worldcup, analytics, x402, cctp)
│   │   └── schemas/        # Pydantic models
│   └── tests/
├── mcp-server/
│   ├── pyproject.toml
│   ├── server.py           # MCP server with 3 tools
│   └── tests/
└── frontend/
    ├── vite.config.ts
    └── src/
        ├── App.tsx         # Router + navbar
        ├── api.ts          # API client
        └── pages/          # Matches, MatchDetail, Leaderboard, Wallet
```

---

## Demo

*Demo video link coming soon — testnet walkthrough of deposit → predict → settle → withdraw cycle.*

---

## Team

Built for The Injective Global Cup hackathon (July 2026).

## License

MIT
