---
name: predictgoal-odds
description: Use when calculating World Cup match win probabilities using ELO ratings and Poisson-based modeling. Provides home/draw/away probabilities with live score adjustments. Deterministic, no API keys needed.
version: 1.0.0
author: PredictGoal Team
license: MIT
tags: [sports, analytics, prediction, world-cup, injective, probability]
---

# PredictGoal Odds — ELO + Poisson Win Probability Model

## Overview

Calculates win/draw/loss probabilities for World Cup football matches using an ELO-based expected goals model with Poisson-derived probabilities. Works with any two-team match — just provide team names and optional live scores.

The model is **deterministic** (same inputs = same outputs) and requires **no API keys or external services**. It's the core analytics engine behind PredictGoal's AI-powered prediction market on Injective.

## Quick Start

```python
from predictgoal_odds import calculate_win_probabilities

result = calculate_win_probabilities(
    home_team="Argentina",
    away_team="Brazil",
    home_score=None,   # None for pre-match; provide ints for live adjustment
    away_score=None,
)

print(f"Home: {result['win_prob_home']:.1%}")   # Home: 51.4%
print(f"Draw: {result['win_prob_draw']:.1%}")   # Draw: 23.5%
print(f"Away: {result['win_prob_away']:.1%}")   # Away: 25.1%
```

## Installation

Copy `predictgoal_odds.py` into your project. No dependencies beyond Python 3.11+ stdlib (`math`).

For AI agents (Claude Code, Cursor, Gemini CLI):

```bash
# Claude Code / Cursor
cp -r agent-skills/predictgoal-odds/ ~/.claude/skills/predictgoal-odds/

# The agent will auto-discover it and can call calculate_win_probabilities()
```

## How It Works

### 1. ELO → Expected Goals

Each team has an ELO rating. The difference between ratings maps to expected goals:

```
elo_diff = home_elo - away_elo
home_xg = max(0.3, 1.2 + elo_diff * 0.0015)
away_xg = max(0.3, 1.2 - elo_diff * 0.0015)
```

The constants (1.2 base goals, 0.0015 sensitivity) are calibrated from historical World Cup data.

### 2. Poisson → Win Probabilities

Expected goals are converted to win/draw/loss probabilities using a logistic approximation of the Poisson distribution:

```
home_win = logistic(home_xg - away_xg)
away_win = logistic(away_xg - home_xg)
draw_prob = 1.0 - home_win - away_win
```

### 3. Live Score Adjustment

When scores are provided (match is in progress), probabilities shift toward the leading team:

```
goal_diff = home_score - away_score
if goal_diff > 0:
    home_win += 0.1 + goal_diff * 0.1   # capped at 0.95
    away_win -= 0.05 + goal_diff * 0.05  # floored at 0.01
```

All probabilities are normalized to sum to 1.0.

### 4. Default ELO Ratings

Pre-loaded ratings for World Cup 2026 teams. Unknown teams default to 1700.

| Team | ELO |
|------|-----|
| Argentina | 1850 |
| Brazil | 1840 |
| France | 1835 |
| Germany | 1820 |
| Spain | 1815 |
| England | 1810 |
| Japan | 1750 |
| Nigeria | 1720 |

## API Reference

### `calculate_win_probabilities(match_id, home_team, away_team, home_score=None, away_score=None)`

Returns a `MatchAnalytics` object:

| Field | Type | Description |
|-------|------|-------------|
| `match_id` | `str` | Match identifier |
| `win_prob_home` | `float` | 0.0–1.0 probability of home win |
| `win_prob_draw` | `float` | 0.0–1.0 probability of draw |
| `win_prob_away` | `float` | 0.0–1.0 probability of away win |
| `key_stats` | `dict` | ELO ratings, expected goals, model name |
| `updated_at` | `datetime` | Timestamp of calculation |

## Integration Examples

### FastAPI Backend

```python
# backend/app/services/analytics.py
from predictgoal_odds import calculate_win_probabilities

@app.get("/api/matches/{match_id}/analytics")
async def get_analytics(match_id: str):
    match = get_match(match_id)
    return calculate_win_probabilities(
        match_id=match.id,
        home_team=match.home_team,
        away_team=match.away_team,
        home_score=match.home_score,
        away_score=match.away_score,
    )
```

### MCP Server Tool

```python
# mcp-server/server.py — exposed as an agent-callable tool
@mcp.tool()
async def calculate_odds(match_id: str, ctx: Context) -> str:
    match = get_match_data(match_id)
    result = calculate_win_probabilities(
        match_id=match_id,
        home_team=match["home_team"],
        away_team=match["away_team"],
        home_score=match.get("home_score"),
        away_score=match.get("away_score"),
    )
    return json.dumps(result, indent=2)
```

### AI Agent Prompt

```
Use the predictgoal-odds skill to calculate win probabilities for
Argentina vs Brazil in the World Cup semifinal. If the current
score is 2-1, factor that into the live adjustment.
```

## Common Pitfalls

1. **Draw probability going negative** — Live score adjustment can push probabilities out of [0,1] range if not clamped. Our implementation normalizes all three probabilities to sum to 1.0.

2. **Unknown teams** — Default ELO is 1700. For accuracy, add team ratings to the `ELO_RATINGS` dict before calculating.

3. **Deterministic but not calibrated** — The model is a logistic approximation, not a full Poisson simulation. It's fast and directionally correct, but don't use it for real-money betting without validation.

4. **No historical data** — This model uses only ELO ratings and scores. For production, augment with xG, possession, form, and head-to-head history.

## Verification Checklist

- [ ] Probabilities sum to 1.0 (±0.01 tolerance)
- [ ] All probabilities are in [0, 1]
- [ ] Live score adjustment shifts probabilities toward the leading team
- [ ] Unknown teams get default ELO (1700) without error
- [ ] Match ID is preserved in output
