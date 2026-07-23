# ⚽ PredictGoal — World Cup Prediction Market + AI Analytics

**Hackathon:** The Injective Global Cup (Jul 3–26, 2026)
**Built with:** x402, CCTP, MCP Server, Agent Skills
**Live:** [Replit (backend)](https://206c7395-fbf5-4c31-8e1e-29869be0e5f1-00-aj5c7akdsj57.kirk.replit.dev/api) | [Vercel (frontend)](https://predict-goal-red.vercel.app/)
**Tests:** 30 passing (24 backend + 6 MCP)

A non-custodial, micro-stakes prediction market for World Cup 2026 matches with real-time AI-powered win probabilities — built on Injective's newest technologies. **Testnet only. Zero real funds.**

---

## What It Does

World Cup fans can:
- Browse **World Cup 2026 matches** with real data from football-data.org (104 matches when API key is set; 4 demo placeholder matches otherwise)
- View **AI-generated win probabilities** (Home/Draw/Away) via ELO + Poisson scoreline simulation
- Place **micro-stake predictions** (1–100 USDC stake + 2 USDC x402 fee) via Injective x402 pay-per-use — a single MetaMask connection is both your **account** and the **fee payer** (no separate address to type)
- Get **premium AI insights** — momentum, form analysis, key player impact (x402-gated)
- Compete on a global **leaderboard** (all predictions tracked, ranked by total won)
- Deposit and withdraw testnet USDC via **CCTP** cross-chain bridge (stubbed)
- Markets are **auto-settled** when the football-data feed reports a finished match with a score (background sweeper), and can also be manually settled via the backend API or MCP Server agent
- **Agent Skills package** (`predictgoal-odds`) — installable by Claude Code/Cursor/Gemini CLI

---

## How Injective Technologies Are Used

### 🔐 x402 — Pay-per-Use Prediction + Premium Insights

Every prediction (`POST /api/predictions`) and premium insight (`GET /api/insights/{match_id}`) is wired for an **x402 payment proof** (2.0 / 3.0 USDC) on the Injective EVM testnet (chain 1439). Enforcement is controlled by `X402_MODE` — it defaults to **`passthrough`** for the hackathon demo, so no real on-chain fee is charged (zero real funds). In passthrough the client still shows a clearly-labeled **"x402 · dev-mode passthrough — no charge"** state when you unlock, so the pay-per-use flow is visible.

**Frontend is wired with a single wallet:** the **Connect Wallet** button connects MetaMask, which is simultaneously the user's **account identity** (where bets & balance are stored) and the **x402 payer** that signs the fee. The browser client (`src/x402Client.ts`) is pinned to the **Injective EVM testnet (chain 1439)** — note `888` is the Injective *Cosmos* testnet id; `1439` is the EVM chain id the dApp uses — and wraps `fetch` with `@x402/fetch`'s `wrapFetchWithPaymentFromConfig` + `@x402/evm`'s `ExactEvmScheme`. Every API call routes through that wrapped fetch once the wallet is connected, so a `POST /api/predictions` (or `GET /api/insights/{id}`) automatically signs a 2.0 / 3.0 USDC payment proof and retries on the `402`. The backend responds with the v2 `X-Payment-Requirements` envelope (CORS-exposed), which the client parses and pays.

| Endpoint | Price | Status |
|----------|-------|--------|
| `POST /api/predictions` | 2.0 USDC | **Wired** — frontend signs proof via MetaMask (Injective EVM testnet chain 1439); enforced when `X402_MODE=enforce` |
| `GET /api/insights/{id}` | 3.0 USDC | **Wired** — x402 flow surfaced in Match Detail "Premium Insights" panel; dev-mode passthrough in the demo |
| `POST /api/wallet/withdraw` | 0.5 USDC | Stubbed |

**Implementation:** `backend/app/services/x402.py` — uses the `x402[fastapi,evm]` Python SDK for the x402 v2 payment flow (network `eip155:1439`, Injective EVM testnet). `X402_MODE` (default `passthrough`) controls enforcement; flip to `enforce` only with a working facilitator + supported chain. Frontend: `src/x402Client.ts` (pinned to Injective EVM chain 1439), `src/api.ts` (`getPaymentFetch()`), `src/components/ConnectPayment.tsx` (the single wallet button).

**Config (production):** `X402_NETWORK` is `eip155:1439` (Injective EVM testnet — the real EVM chain id; `888` is the Injective *Cosmos* testnet id) in `backend/app/services/x402.py`, and `X402_MODE` defaults to `passthrough`. Set `X402_PAYMENT_RECIPIENT` to your Injective EVM `0x` address (the one MetaMask shows after adding the Injective EVM testnet), **not** the `inj1` Cosmos address. **Important:** no hosted x402 facilitator exists for Injective, so `X402_MODE=passthrough` is correct for the demo — the in-app USDC balance is still debited per prediction, but no real on-chain fee is charged (zero real funds). The client surfaces a clearly-labeled **"x402 · dev-mode passthrough — no charge"** state on unlock. Real x402 enforcement on Injective would require a self-hosted facilitator that supports chain 1439. Leave `X402_MODE=passthrough` (default) for the demo.

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
| Match data | **Live** | football-data.org API with 60s cache (4 demo placeholders if no key) |
| AI win probabilities | **Live** | ELO + Poisson scoreline simulation, deterministic |
| Predictions (CRUD) | **Live** | Persistent JSON store, locked at kickoff |
| Leaderboard | **Live** | Server-computed, all predictions tracked |
| Settlement | **Live** | Auto-settles finished matches from the football-data feed (background sweeper, idempotent + reentrancy-safe); also admin-key gated manual endpoint; credits winners |
| x402 fee deduction | **Live** | 2 USDC deducted from balance per prediction |
| Premium insights | **x402-gated (dev-mode passthrough)** | x402 pay-per-use (3.0 USDC) is fully wired on Injective EVM testnet (chain 1439), but `X402_MODE=passthrough` means no real on-chain fee is charged (in-app USDC balance still debited per prediction). The client shows a labeled "x402 · dev-mode passthrough" state on unlock. Insight *content* (momentum, form, key-player) is **simulated** from the ELO model — not real match data |
| CCTP deposit/withdraw | **Stubbed** | Returns success with mock tx hash; real testnet CCTP requires Injective-side Circle support |
| MCP Server settlement | **Live** | Local stdio only, not connected to backend |
| Agent Skills package | **Live** | Drop-in module, works standalone |
| Persistent storage | **Live** | JSON file-backed store on an attached Render persistent disk (`/data`, via `STORE_PATH`); survives deploys. Local dev uses `backend/data/` (gitignored) |
| Health check endpoint | **Live** | GET + HEAD at /health, toggle with HEALTH_CHECK_ENABLED |

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
│ - Leaderboard│     │ - Store      │
│ - Wallet     │     │   (balances  │
└──────────────┘     │    + bets)   │
                     └──────┬───────┘
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

## Security

- **Per-user locking** — asyncio.Lock per address prevents concurrent stake races
- **Balance locking** — thread-safe read-modify-write on all credit/debit operations
- **Kickoff cutoff** — server-side enforcement (no post-kickoff/live predictions)
- **Match ID validation** — checked against real match data, not trusted from request
- **Settlement auth** — the manual settlement endpoint requires the admin key (rejects if not configured); automatic settlement is a server-internal trusted process (no key needed)
- **Idempotent settlement** — calling twice returns "already_settled"
- **Reentrancy-safe** — per-match asyncio.Lock prevents double-payouts
- **Winning balances credited** — settlement auto-credits winners with 2x payout
- **Input validation** — Pydantic with strict enums, `extra=forbid`
- **No stack traces** — global exception handler
- **Rate limiting** — slowapi (60 req/min default)
- **CORS** — restricted to configured origins
- **Secrets** — `.env` only, `.gitignore` enforced, `.env.example` with placeholders
- **No default address** — all endpoints require explicit `X-User-Address` header
- **MCP admin key** — loaded from `.env`, never hardcoded

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
# Set ADMIN_SETTLE_KEY for the manual settlement endpoint (recommended; admin-key gated)
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

> **Note:** The frontend talks to the backend via `/api` (Vite dev proxy). For a production build served separately from the API, set `VITE_API_BASE` to your backend URL (e.g. `https://predictgoal.onrender.com/api`) in a `.env` file in `frontend/`.

Open http://localhost:5173

> **Wallet setup:** PredictGoal uses a single MetaMask wallet as both your account and the x402 fee payer. Add the **Injective EVM Testnet** to MetaMask before connecting: Network Name `Injective EVM Testnet`, RPC URL `https://k8s.testnet.json-rpc.injective.network`, Chain ID `1439` (the EVM chain id — note `888` is the Injective *Cosmos* testnet id), Currency `INJ`. The 2 / 3 USDC fee would be paid there (in the demo it runs in x402 dev-mode passthrough, so nothing is actually charged).

### Agent Skills
```bash
# Copy to Claude Code or Cursor skills directory
cp -r agent-skills/predictgoal-odds/ ~/.claude/skills/

# Or run directly
python agent-skills/predictgoal-odds/predictgoal_odds.py Spain Belgium
```

### Demo odds (quick CLI)
```bash
cd mcp-server && uv run python demo_odds.py Spain Belgium
```

### Run all tests
```bash
cd backend && uv run pytest tests/ -v    # 24 tests
cd mcp-server && uv run pytest tests/ -v  # 6 tests
```

---

## API Endpoints

| Method | Path | Description | Auth | Price |
|--------|------|-------------|------|-------|
| GET | `/api/matches` | List all matches | — | Free |
| GET | `/api/matches/{id}` | Match detail | — | Free |
| GET | `/api/matches/{id}/analytics` | Win probabilities | — | Free |
| GET | `/api/insights/{id}` | Premium AI insight | x402 | 3.0 USDC |
| POST | `/api/predictions` | Place prediction | Wallet addr | 2.0 USDC |
| GET | `/api/predictions/me` | My predictions | Wallet addr | Free |
| GET | `/api/predictions/leaderboard` | Leaderboard (all predictions) | — | Free |
| POST | `/api/predictions/settle` | Admin settlement | Admin key | Free |
| GET | `/api/wallet/balance` | Check USDC balance | Wallet addr | Free |
| POST | `/api/wallet/deposit` | CCTP deposit | Wallet addr | Free |
| POST | `/api/wallet/withdraw` | CCTP withdraw | Wallet addr | 0.5 USDC |
| GET | `/health` | Health check (GET + HEAD) | — | Free |

---

## Project Structure

```
predictgoal/
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
│   │   ├── main.py              # FastAPI entry + rate limiting + health
│   │   ├── store.py             # Persistent JSON store (balances + predictions)
│   │   ├── core/config.py       # Settings from env
│   │   ├── api/                 # Routers (matches, predictions, wallet, insights)
│   │   ├── services/            # Business logic (worldcup, analytics, x402, cctp, balance)
│   │   └── schemas/             # Pydantic models
│   └── tests/
├── mcp-server/
│   ├── pyproject.toml
│   ├── MCP_README.md            # Claude Desktop / Cursor setup
│   ├── server.py                # MCP server with 3 tools
│   ├── demo_odds.py             # Quick CLI demo: python demo_odds.py Spain Belgium
│   └── tests/
└── frontend/
    ├── package.json
    ├── vercel.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx              # Router + navbar + wallet state
        ├── api.ts               # API client
        └── components/
        │   └── ConnectPayment.tsx # Single MetaMask wallet (account + x402 payer)
        └── pages/               # Matches, MatchDetail, Leaderboard, Wallet
```

---

## Hackathon Judging Criteria Map

| Criterion | Where to find it |
|-----------|-----------------|
| **x402 usage** | `backend/app/services/x402.py` (testnet-ready), x402 fee deducted from balance, premium insights endpoint |
| **CCTP usage** | `backend/app/services/cctp.py`, wallet API, honest stub documentation |
| **MCP Server** | `mcp-server/server.py` (3 tools), `mcp-server/MCP_README.md` (Claude/Cursor setup) |
| **Agent Skills** | `agent-skills/predictgoal-odds/` (installable SKILL.md + Python module) |
| **Injective integrated** | x402 pricing, CCTP stubs, testnet config, Injective RPC/chain_id |
| **Problem solved** | README "What It Does" section |
| **User experience** | `frontend/` — filters, flags, predictions, leaderboard, wallet, potential win display |
| **Security** | Admin auth, settlement idempotency, input validation, per-user locks, balance locking |
| **Data persistence** | `backend/app/store.py` — JSON file store survives Render restarts |

---

## License

MIT
