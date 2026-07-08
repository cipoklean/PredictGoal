"""Analytics service — calculates win probabilities and match insights."""

import random
import math
from datetime import datetime, timezone

from app.schemas.match import MatchAnalytics


# Simulated ELO ratings for demo purposes (stored in-memory)
_ELO_RATINGS: dict[str, float] = {
    "Argentina": 1850,
    "Brazil": 1840,
    "France": 1835,
    "Germany": 1820,
    "Spain": 1815,
    "England": 1810,
    "Japan": 1750,
    "Nigeria": 1720,
    "TBD": 1700,
}


def calculate_win_probabilities(
    match_id: str,
    home_team: str,
    away_team: str,
    home_score: int | None = None,
    away_score: int | None = None,
) -> MatchAnalytics:
    """
    Calculate win/draw probabilities using a Poisson-based model.

    For demo purposes, uses ELO ratings + score adjustments.
    In production, this would use historical data + ML model.
    """
    home_elo = _ELO_RATINGS.get(home_team, 1700)
    away_elo = _ELO_RATINGS.get(away_team, 1700)

    # ELO to expected goals (simplified Poisson model)
    elo_diff = home_elo - away_elo
    home_xg = max(0.3, 1.2 + elo_diff * 0.0015)
    away_xg = max(0.3, 1.2 - elo_diff * 0.0015)

    # Proper Poisson simulation: sum over all scorelines 0..10
    home_win, draw_prob, away_win = _poisson_sim(home_xg, away_xg)

    # If match is live, adjust based on current score
    if home_score is not None and away_score is not None:
        goal_diff = home_score - away_score
        if goal_diff > 0:
            # Leading team has higher win probability
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

    return MatchAnalytics(
        match_id=match_id,
        win_prob_home=round(home_win, 4),
        win_prob_draw=round(draw_prob, 4),
        win_prob_away=round(away_win, 4),
        key_stats={
            "home_elo": home_elo,
            "away_elo": away_elo,
            "home_xg": round(home_xg, 2),
            "away_xg": round(away_xg, 2),
            "model": "ELO + Poisson (simplified)",
        },
        updated_at=datetime.now(timezone.utc),
    )


def _poisson_prob(k: int, lam: float) -> float:
    """Poisson probability mass function: P(X = k)."""
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def _poisson_sim(home_xg: float, away_xg: float, max_goals: int = 10) -> tuple[float, float, float]:
    """Simulate home_win / draw / away_win by summing Poisson scoreline probabilities."""
    home_win = 0.0
    draw_prob = 0.0
    away_win = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob = _poisson_prob(i, home_xg) * _poisson_prob(j, away_xg)
            if i > j:
                home_win += prob
            elif i == j:
                draw_prob += prob
            else:
                away_win += prob
    return home_win, draw_prob, away_win
