"""Demo: calculate odds for any World Cup match by team names."""
import sys

# If teams passed, use them. Default: Argentina vs Brazil
if len(sys.argv) >= 3:
    home, away = sys.argv[1], sys.argv[2]
else:
    home, away = "Argentina", "Brazil"

sys.path.insert(0, "../agent-skills/predictgoal-odds")
from predictgoal_odds import calculate_win_probabilities, ELO_RATINGS

result = calculate_win_probabilities("DEMO", home, away)

print(f"\n  {home} ({ELO_RATINGS.get(home, '?')} ELO) vs {away} ({ELO_RATINGS.get(away, '?')} ELO)")
print(f"  Home: {result.win_prob_home:.1%}  "
      f"Draw: {result.win_prob_draw:.1%}  "
      f"Away: {result.win_prob_away:.1%}")
print(f"  xG: {result.key_stats.get('home_xg','?')} — {result.key_stats.get('away_xg','?')}")
print(f"  Total: {result.win_prob_home + result.win_prob_draw + result.win_prob_away:.4f}")
print()
