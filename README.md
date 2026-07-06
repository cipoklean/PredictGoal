# ⚽ PredictGoal — World Cup Prediction Market + AI Analytics

**Hackathon:** The Injective Global Cup (Jul 3–19, 2026)
**Built with:** x402, CCTP, MCP Server, Agent Skills
**Live:** [predictgoal.onrender.com](https://predictgoal.onrender.com) (backend) | Vercel (frontend)
**Tests:** 29 passing (23 backend + 6 MCP)

A non-custodial, micro-stakes prediction market for World Cup 2026 matches with real-time AI-powered win probabilities — built on Injective's newest technologies. **Testnet only. Zero real funds.**

---

## What It Does

World Cup fans can:
- Browse **104 live World Cup 2026 matches** with real data from football-data.org
- View **AI-generated win probabilities** (Home/Draw/Away) via ELO + Poisson model
- Place **micro-stake predictions** (0.1–100 USDC) via Injective x402 pay-per-use
- Get **premium AI insights** — momentum, form analysis, key player impact (x402-gated)
- Compete on a global **leaderboard** (settled predictions only)
- Deposit and withdraw testnet USDC via **CCTP** cross-chain bridge (stubbed)
- Markets are **auto-settled** post-match via backend API or MCP Server agent
- **Agent Skills package** (`predictgoal-odds`) — installable by Claude Code/Cursor/Gemini CLI

---

## How Injective Technologies Are Used

### 🔐 x402 — Pay-per-Use Prediction + Premium Insights

Every prediction (`POST /api/predictions`) and premium insight (`GET /api/insights/{match_id}`) requires an **x402 payment proof** header. The backend validates the payment on Injective testnet before accepting the request.

| Endpoint | Price | Status |
|----------|-------|--------|
| `POST /api/predictions` | 0.1 USDC | Dev mode (passthrough) |
| `GET /api/insights/{id}` | 0.5 USDC | Testnet-ready (x402 facilitator) |
| `POST /api/wallet/withdraw` | 0.5 USDC | Stubbed |

**Implementation:** `backend/app/services/x402.py` — uses the `x402[fastapi,evm]` Python SDK with the free x402.org facilitator for testnet payment verification. Falls back to dev-mode passthrough when no payment recipient is configured.

### 🌉 CCTP — Cross-Chain USDC Transfers

Users can **deposit USDC from other testnets to Injective testnet** and **withdraw back** using Circle's Cross-Chain Transfer Protocol.

**Status:** Stubbed. The architecture is designed for CCTP flow:
1. User approves USDC spend on source chain
2. Calls `depositForBurn` on TokenMessenger
3. Waits for Circle attestation
4. Calls `receiveMessage` on Injective

**Implementation:** `backend/app/services/cctp.py` + `backend/app/api/wallet.py`

### 🤖 MCP Server — 3 Agent Tools

Standalone Model Context Protocol server (stdio transport). Connect from Claude Desktop, Cursor, or Hermes.

| Tool | Description | Security |
|------|-------------|----------|
| `get_match_data` | Fetch match info + live scores | Read-only |
| `calculate_odds` | ELO + Poisson win probabilities | Deterministic |
| `settle_market` | Admin-gated settlement | Reentrancy lock + idempotency |

**Implementation:** `mcp-server/server.py` — FastMCP with three registered tools.
**Setup docs:** `mcp-server/MCP_README.md`

### 🧠 Agent Skills — installable `predictgoal-odds` Package

The ELO + Poisson model is packaged as an **installable skill** that Claude Code, Cursor, and Gemini CLI can discover and execute.

```
agent-skills/predictgoal-odds/
├── SKILL.md              # Skill manifest with usage docs
└── predictgoal_odds.py   # Self-contained Python module (stdlib only)
```

AI agents can call `calculate_win_probabilities(home_team, away_team, ...)` to get deterministic win probabilities with live score adjustment.

---

## Live vs. Stubbed — Honesty Statement

| Feature | Status | Notes |
|---------|--------|-------|
| Match data (104 matches) | **Live** | football-data.org API with 60s cache |
| AI win probabilities | **Live** | ELO + Poisson model, deterministic |
| Predictions (CRUD) | **Live** | In-memory store, locked at kickoff |
| Leaderboard | **Live** | Server-computed, settled-only |
| Settlement | **Live** | Admin-key gated, idempotent, reentrancy-safe |
| Premium insights | **x402-gated** | Real verification via x402.org facilitator (Base Sepolia) |
| x402 payment verification | **Testnet-ready** | Uses x402.org facilitator; falls back to dev mode if not configured |
| CCTP deposit/withdraw | **Stubbed** | Returns success with mock tx hash; real testnet CCTP requires Injective-side Circle support |
| MCP Server settlement | **Live** | Local stdio only, not connected to backend |
| Agent Skills package | **Live** | Drop-in module, works standalone |

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌───────────────┐
│  React/Vite  │────▶│   FastAPI    │────▶│  Injective     │
│  Frontend    │     │   Backend    │     │  Testnet       │
│              │     │              │     │  (x402, CCTP)  │
│ - Matches    │     │ - Auth mw    │     └───────────────┘
│ - Flags      │     │ - Cache 60s  │
│ - Predict UI │     │ - Settlement │
│ - Analytics  │     │ - Insights   │
│ - Leaderboard│     └──────┬───────┘
│ - Wallet     │            │
└──────────────┘            ▼
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

## Security

- **Per-user locking** — asyncio.Lock per address prevents concurrent stake races
- **Kickoff cutoff** — server-side enforcement (no post-kickoff/live predictions)
- **Knockout draw blocked** — M49+ matches can only bet home/away
- **Match ID validation** — checked against real match data, not trusted from request
- **Settlement auth** — admin key required; idempotent + reentrancy-safe
- **Input validation** — Pydantic with strict enums, `extra=forbid`
- **No stack traces** — global exception handler
- **Rate limiting** — slowapi (60 req/min default)
- **CORS** — restricted to Vercel origin, not `*`
- **Secrets** — `.env` only, `.gitignore` enforced, `.env.example` with placeholders

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

### Agent Skills
```bash
# Copy to Claude Code or Cursor skills directory
cp -r agent-skills/predictgoal-odds/ ~/.claude/skills/
```

### Run all tests
```bash
cd backend && uv run pytest tests/ -v    # 23 tests
cd mcp-server && uv run pytest tests/ -v  # 6 tests
```

---

## API Endpoints

| Method | Path | Description | Auth | Price |
|--------|------|-------------|------|-------|
| GET | `/api/matches` | List all matches | — | Free |
| GET | `/api/matches/{id}` | Match detail | — | Free |
| GET | `/api/matches/{id}/analytics` | Win probabilities | — | Free |
| GET | `/api/insights/{id}` | Premium AI insight | x402 | 0.5 USDC |
| POST | `/api/predictions` | Place prediction | Wallet addr | 0.1 USDC |
| GET | `/api/predictions/me` | My predictions | Wallet addr | Free |
| GET | `/api/predictions/leaderboard` | Leaderboard (settled only) | — | Free |
| POST | `/api/predictions/settle` | Admin settlement | Admin key | Free |
| POST | `/api/wallet/deposit` | CCTP deposit | Wallet addr | Free |
| POST | `/api/wallet/withdraw` | CCTP withdraw | Wallet addr | 0.5 USDC |
| GET | `/health` | Health check | — | Free |

---

## Project Structure

```
predictgoal/
├── SPEC.md                      # Design spec
├── README.md                    # This file
├── render.yaml                  # Render Blueprint
├── runtime.txt                  # Python version for Render
├── agent-skills/
│   └── predictgoal-odds/        # Installable Agent Skill
│       ├── SKILL.md
│       └── predictgoal_odds.py
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py              # FastAPI entry + rate limiting
│   │   ├── core/config.py       # Settings from env
│   │   ├── api/                 # Routers (matches, predictions, wallet, insights)
│   │   ├── services/            # Business logic (worldcup, analytics, x402, cctp)
│   │   └── schemas/             # Pydantic models
│   └── tests/
├── mcp-server/
│   ├── pyproject.toml
│   ├── MCP_README.md            # Claude Desktop / Cursor setup
│   ├── server.py                # MCP server with 3 tools
│   └── tests/
└── frontend/
    ├── package.json
    ├── vercel.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx              # Router + glass navbar + ConnectWallet
        ├── api.ts               # API client
        ├── components/
        │   └── ConnectWallet.tsx
        └── pages/               # Matches, MatchDetail, Leaderboard, Wallet
```

---

## Demo Video Script (Suggested)

1. **Open PredictGoal** — show dark Linear-style UI, 104 matches with flags
2. **Filter to upcoming** — pick a scheduled match, view AI probabilities
3. **Place prediction** — select outcome, enter stake, click Predict → success
4. **View leaderboard** — show ranking with settled predictions
5. **Premium insight** — demonstrate `/api/insights/WC2026-M59` with momentum + form
6. **Admin settlement** — call `/api/predictions/settle` with admin key → settled
7. **Verify idempotency** — settle again → "already_settled"
8. **MCP Server** — show Claude Desktop calling `calculate_odds`
9. **Agent Skills** — show `python predictgoal_odds.py Argentina Brazil`

---

## Hackathon Judging Criteria Map

| Criterion | Where to find it |
|-----------|-----------------|
| **x402 usage** | `backend/app/services/x402.py`, premium insights endpoint, README pricing table |
| **CCTP usage** | `backend/app/services/cctp.py`, wallet API, honest stub documentation |
| **MCP Server** | `mcp-server/server.py` (3 tools), `mcp-server/MCP_README.md` (Claude/Cursor setup) |
| **Agent Skills** | `agent-skills/predictgoal-odds/` (installable SKILL.md + Python module) |
| **Injective integrated** | x402 pricing, CCTP stubs, testnet config, Injective RPC/chain_id |
| **Problem solved** | README "What It Does" section |
| **User experience** | `frontend/` — filters, flags, predictions, leaderboard, wallet |

---

## License

MIT
