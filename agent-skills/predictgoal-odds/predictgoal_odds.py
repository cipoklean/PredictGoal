"""
PredictGoal Odds — ELO + Poisson win probability model.

Self-contained, no dependencies beyond Python stdlib.
Drop this file anywhere and import calculate_win_probabilities().
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


# Default ELO ratings for World Cup 2026 teams
ELO_RATINGS: dict[str, float] = {
    "Argentina": 1850, "Brazil": 1840, "France": 1835, "Germany": 1820,
    "Spain": 1815, "England": 1810, "Japan": 1750, "Nigeria": 1720,
    "Mexico": 1730, "South Africa": 1680, "South Korea": 1740, "Czechia": 1710,
    "Canada": 1690, "Bosnia-Herzegovina": 1670, "United States": 1720,
    "Paraguay": 1660, "Qatar": 1650, "Switzerland": 1780, "Italy": 1830,
    "Netherlands": 1825, "Portugal": 1810, "Belgium": 1830, "Croatia": 1785,
    "Senegal": 1725, "Uruguay": 1790, "Denmark": 1770, "Australia": 1680,
    "Morocco": 1710, "Ghana": 1690, "Cameroon": 1670, "Ecuador": 1685,
    "Saudi Arabia": 1660, "Tunisia": 1690, "Poland": 1750, "Serbia": 1730,
    "Sweden": 1760, "Norway": 1755, "Austria": 1740, "Egypt": 1680,
    "Algeria": 1695, "Ivory Coast": 1715, "Colombia": 1775, "Chile": 1760,
    "Peru": 1710, "Turkey": 1745, "Ukraine": 1720, "Romania": 1690,
    "Scotland": 1705, "Wales": 1700, "Hungary": 1695, "Slovakia": 1680,
    "Greece": 1685, "New Zealand": 1630, "Costa Rica": 1670, "Panama": 1640,
    "Mali": 1650, "Burkina Faso": 1640, "DR Congo": 1630, "Zambia": 1620,
    "TBD": 1700,
}


@dataclass
class MatchAnalytics:
    match_id: str
    win_prob_home: float
    win_prob_draw: float
    win_prob_away: float
    key_stats: dict
    updated_at: datetime


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


def calculate_win_probabilities(
    match_id: str,
    home_team: str,
    away_team: str,
    home_score: Optional[int] = None,
    away_score: Optional[int] = None,
) -> MatchAnalytics:
    """
    Calculate win/draw/loss probabilities using ELO + Poisson model.

    Args:
        match_id: Match identifier (e.g. 'WC2026-M1')
        home_team: Home team name
        away_team: Away team name
        home_score: Current home score (None for pre-match)
        away_score: Current away score (None for pre-match)

    Returns:
        MatchAnalytics with probabilities in [0, 1] summing to ~1.0
    """
    home_elo = ELO_RATINGS.get(home_team, 1700)
    away_elo = ELO_RATINGS.get(away_team, 1700)

    # ELO → expected goals
    elo_diff = home_elo - away_elo
    home_xg = max(0.3, 1.2 + elo_diff * 0.0015)
    away_xg = max(0.3, 1.2 - elo_diff * 0.0015)

    # Proper Poisson simulation: sum over all scorelines 0..10
    home_win, draw_prob, away_win = _poisson_sim(home_xg, away_xg)

    # Live match adjustment
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
            "model": "ELO + Poisson (logistic approximation)",
        },
        updated_at=datetime.now(timezone.utc),
    )


# ── CLI demo ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        home, away = sys.argv[1], sys.argv[2]
        hs = int(sys.argv[3]) if len(sys.argv) > 3 else None
        aws = int(sys.argv[4]) if len(sys.argv) > 4 else None
        result = calculate_win_probabilities("CLI", home, away, hs, aws)
    else:
        # Demo with Argentina vs Brazil
        result = calculate_win_probabilities("WC2026-M1", "Argentina", "Brazil")

    print(f"\n  {result.match_id}: {result.key_stats.get('home_elo', '?')} vs "
          f"{result.key_stats.get('away_elo', '?')} ELO")
    print(f"  Home: {result.win_prob_home:.1%}  "
          f"Draw: {result.win_prob_draw:.1%}  "
          f"Away: {result.win_prob_away:.1%}")
    print(f"  xG: {result.key_stats.get('home_xg', '?')} — "
          f"{result.key_stats.get('away_xg', '?')}")
    print(f"  Total: {result.win_prob_home + result.win_prob_draw + result.win_prob_away:.4f}")
    print()
