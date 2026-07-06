# PredictGoal — Prediction Market + AI Analytics

**Hackathon:** The Injective Global Cup (Jul 3–19, 2026)
**Track:** Top 3 Projects ($150 each) + Points Contest + Goal Battle
**Repo:** `github.com/<user>/predictgoal` (to be created)
**Stack:** React + Vite + Tailwind (frontend) | FastAPI + Injective SDK (backend) | MCP Server (agent tools)

---

## 1. Problem Statement

World Cup fans want to engage with matches beyond passive viewing. Existing prediction markets are either:
- Custodial / centralized (trust issues)
- Complex UX (high barrier)
- No AI-powered insights (blind betting)

**Solution:** A non-custodial, micro-stakes prediction market with real-time AI match analytics — built on Injective's new primitives.

---

## 2. Core Features (MVP Scope)

| Feature | Description | Injective Tech |
|---------|-------------|----------------|
| **Match Discovery** | Live World Cup matches with real-time stats | World Cup API (external) |
| **Place Prediction** | Predict match outcome (Home/Draw/Away) with micro-stakes USDC | **x402** (pay-per-prediction), **CCTP** (cross-chain USDC deposit) |
| **AI Analytics** | Win probabilities, key player stats, momentum indicators | **Agent Skills** (analytics agent), **MCP Server** (tool orchestration) |
| **Auto-Settlement** | Post-match, agent verifies result & distributes rewards | **MCP Server** (settlement tool), **CCTP** (payout) |
| **Leaderboard** | Global + per-match rankings | — |
| **Demo Mode** | Play with testnet faucet USDC (no real funds) | Injective Testnet |

---

## 3. Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI        │────▶│  Injective      │
│   (React/Vite)  │     │   Backend        │     │  Testnet        │
│                 │     │                  │     │                 │
│ - Match list    │     │ - x402 middleware│     │ - x402 settlement│
│ - Predict UI    │     │ - CCTP deposit/  │     │ - CCTP bridge   │
│ - Analytics     │     │   withdraw       │     │ - WASM contracts│
│ - Leaderboard   │     │ - MCP client     │     │                 │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │   MCP Server     │
                        │   (Agent Skills) │
                        │                  │
                        │ Tools:           │
                        │ - get_match_data │
                        │ - calculate_odds │
                        │ - settle_market  │
                        └──────────────────┘
```

---

## 4. Data Models

### Match
```python
match_id: str              # "WC2026-M1"
home_team: str
away_team: str
kickoff_utc: datetime
status: enum[scheduled, live, finished, cancelled]
home_score: int | null
away_score: int | null
odds_home: float           # AI-calculated
odds_draw: float
odds_away: float
```

### Prediction (User Position)
```python
prediction_id: uuid
user_address: str          # Injective/EVM address
match_id: str
outcome: enum[home, draw, away]
stake_usdc: Decimal        # micro-stakes (e.g., 0.1 USDC)
placed_at: datetime
tx_hash: str               # x402 payment proof
settled: bool
payout_usdc: Decimal | null
```

### Analytics Snapshot (per match, cached 60s)
```python
match_id: str
win_prob_home: float
win_prob_draw: float
win_prob_away: float
key_stats: dict            # possession, shots, xG, momentum
updated_at: datetime
```

---

## 5. API Contract (FastAPI)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/matches` | — | List all World Cup matches |
| GET | `/api/matches/{id}` | — | Match detail + analytics |
| GET | `/api/matches/{id}/analytics` | — | AI win probabilities + stats |
| POST | `/api/predictions` | x402 | Place prediction (pay-per-use) |
| GET | `/api/predictions/me` | Wallet sig | User's predictions |
| POST | `/api/deposit` | Wallet sig | CCTP deposit USDC (testnet) |
| POST | `/api/withdraw` | Wallet sig | CCTP withdraw USDC |
| GET | `/api/leaderboard` | — | Global rankings |

**x402 Middleware:** Every write endpoint (`/predictions`, `/deposit`, `/withdraw`) requires valid x402 payment header. Amount = stake + protocol fee (0.5%).

---

## 6. MCP Server Tools (Agent Skills)

| Tool | Input | Output | Security |
|------|-------|--------|----------|
| `get_match_data` | `match_id` | Match object + live stats | Read-only, cached |
| `calculate_odds` | `match_id` + live stats | `{home, draw, away}` probabilities | Pure function, deterministic |
| `settle_market` | `match_id` + final score | List of winning predictions + payouts | **Admin-only** (MCP server key), idempotent |

**Settlement Logic (critical path):**
```
1. Verify match.status == finished
2. Fetch all unresolved predictions for match
3. For each: if prediction.outcome == actual_outcome → winner
4. Payout = stake * (total_pool / winning_pool) * (1 - protocol_fee)
5. Batch CCTP transfer to winners
6. Mark predictions settled + record tx hashes
7. Emit event for frontend polling
```
**Guards:** Reentrancy lock per match, idempotency key (match_id), max 1 settlement per match.

---

## 7. Smart Contracts (Injective WASM — Optional for MVP)

If time permits, minimal contracts for:
- **PredictionMarket** — escrow stakes, settle via admin (MCP server)
- **FeeCollector** — accumulate protocol fees

**MVP Decision:** Skip contracts initially. Use backend escrow + CCTP for speed. Contracts = stretch goal (Day 6).

---

## 8. Security Checklist (Non-Negotiable)

| Area | Measures |
|------|----------|
| **Input Validation** | Pydantic models on every endpoint, strict enums, Decimal for money |
| **Authentication** | Wallet signature verification (SIWE/EIP-191) for user endpoints; x402 for pay-per-use |
| **Authorization** | MCP server key for settlement; admin-only tools |
| **Reentrancy** | `asyncio.Lock` per `match_id` in settlement |
| **Idempotency** | Settlement keyed by `match_id`; duplicate calls no-op |
| **Rate Limiting** | 10 req/min per IP on x402 endpoints; 60 req/min on reads |
| **Funds Handling** | Testnet only; CCTP testnet USDC; no private keys in repo |
| **Error Handling** | No stack traces to client; structured error codes |
| **Logging** | Audit log for every prediction, deposit, withdrawal, settlement |
| **Dependencies** | Pin versions; `pip-audit` in CI |

---

## 9. Testnet Configuration

| Network | Chain ID | RPC | Explorer |
|---------|----------|-----|----------|
| Injective Testnet | `injective-888` | `https://testnet.sentry.tm.injective.network:443` | `https://testnet.explorer.injective.network` |
| CCTP Testnet | Ethereum Sepolia / Arbitrum Sepolia | Via Circle testnet | — |
| USDC Testnet | `0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238` (Sepolia) | — | — |

**Faucets:**
- Injective testnet INJ: `https://testnet.faucet.injective.network`
- Sepolia USDC: Circle testnet faucet

---

## 10. 7-Day Implementation Plan

### Day 1 — Foundation
- [ ] Repo init: monorepo (`/frontend`, `/backend`, `/mcp-server`)
- [ ] Injective dev env: `injectived` testnet, wallet keypair (env)
- [ ] World Cup data source locked (football-data.org API key)
- [ ] SPEC.md finalized (this file)

### Day 2 — x402 + CCTP Core
- [ ] FastAPI project with x402 middleware (Injective Python SDK)
- [ ] CCTP deposit/withdraw endpoints (testnet Circle API)
- [ ] Wallet signature verification (SIWE)
- [ ] Unit tests: payment flow, signature verification

### Day 3 — MCP Server + Agent Skills
- [ ] MCP server (Python `mcp` package) with 3 tools
- [ ] `get_match_data` → football-data.org + cache
- [ ] `calculate_odds` → Poisson-based model (home/away/draw)
- [ ] `settle_market` → admin-gated, reentrancy-locked, idempotent
- [ ] Integration test: full prediction → settlement cycle

### Day 4 — Frontend
- [ ] Vite + React + Tailwind + TypeScript
- [ ] Pages: Matches, Match Detail, Predict, Leaderboard, Wallet
- [ ] Injective wallet adapter (Keplr/Leap)
- [ ] Real-time analytics polling (SSE or 30s interval)
- [ ] x402 payment flow in browser

### Day 5 — Polish & E2E
- [ ] README with Injective tech usage section (required)
- [ ] Demo video script + recording
- [ ] Error boundaries, loading states, empty states
- [ ] Testnet E2E: deposit → predict → wait → settle → withdraw
- [ ] `pip-audit`, `npm audit`, fix criticals

### Day 6 — Deploy & Submit
- [ ] Frontend → Vercel/Netlify
- [ ] Backend → Render/Fly.io (free tier)
- [ ] MCP server → same host as backend
- [ ] Typeform submission
- [ ] X post draft with screenshots + demo link

### Day 7 — Buffer
- [ ] Bug fixes from testnet run
- [ ] Extra polish (animations, copy)
- [ ] Early submit if ready

---

## 11. Stretch Goals (Post-MVP / If Time)

- [ ] WASM PredictionMarket contract (escrow + settle on-chain)
- [ ] Mobile-responsive PWA
- [ ] Social features (share prediction, referrals)
- [ ] Multi-language (EN/ES/PT for World Cup)
- [ ] Historical backtesting page for odds model

---

## 12. Submission Checklist (Hackathon Requirements)

- [ ] GitHub repo with **clear README** explaining:
  - How x402, CCTP, MCP Server, Agent Skills are used
  - Whether/how Injective is integrated
  - What project does, problem solved, user interaction
- [ ] Demo video (≤3 min)
- [ ] Live demo link
- [ ] Typeform submitted: `https://xsxo494365r.typeform.com/to/TMaGb1du`
- [ ] X post with `#InjectiveGlobalCupHackathon` tagging `@injective @NinjaLabsHQ @NinjaLabsCN`

---

## 13. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| World Cup API rate limits | Medium | High | Cache 60s; fallback static fixture file |
| CCTP testnet flaky | Medium | Medium | Mock CCTP in CI; manual testnet verification only |
| x402 SDK bugs | Low | High | Pin SDK version; minimal wrapper |
| Settlement logic bug | Low | Critical | Exhaustive unit tests; property-based testing |
| Time overrun | High | High | Daily standup; cut stretch goals ruthlessly |

---

**Next Action:** Day 1 — Repo init + Injective testnet setup + World Cup API key.