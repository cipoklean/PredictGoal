import { useEffect, useState } from "react";
import { api, LeaderboardEntry } from "../api";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getLeaderboard()
      .then(setEntries)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center p-8 text-gray-400">Loading leaderboard...</div>;

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-3xl font-bold text-white mb-6">Leaderboard</h1>
      {entries.length === 0 ? (
        <p className="text-gray-400 text-center py-8">No predictions yet. Be the first!</p>
      ) : (
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-750 border-b border-gray-700">
              <tr>
                <th className="p-3 text-gray-400 font-medium text-sm">#</th>
                <th className="p-3 text-gray-400 font-medium text-sm">Player</th>
                <th className="p-3 text-gray-400 font-medium text-sm text-right">Wagered</th>
                <th className="p-3 text-gray-400 font-medium text-sm text-right">Won</th>
                <th className="p-3 text-gray-400 font-medium text-sm text-right">Win Rate</th>
                <th className="p-3 text-gray-400 font-medium text-sm text-right">Picks</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.rank} className="border-b border-gray-700/50 hover:bg-gray-750">
                  <td className="p-3 text-white font-bold">
                    {e.rank <= 3 ? ["🥇", "🥈", "🥉"][e.rank - 1] : e.rank}
                  </td>
                  <td className="p-3 text-white font-mono text-sm">
                    {e.user_address.slice(0, 8)}...{e.user_address.slice(-4)}
                  </td>
                  <td className="p-3 text-right text-gray-300">{e.total_wagered.toFixed(1)} USDC</td>
                  <td className="p-3 text-right text-green-400">{e.total_won.toFixed(1)} USDC</td>
                  <td className="p-3 text-right text-yellow-400">{(e.win_rate * 100).toFixed(1)}%</td>
                  <td className="p-3 text-right text-gray-400">{e.predictions_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
