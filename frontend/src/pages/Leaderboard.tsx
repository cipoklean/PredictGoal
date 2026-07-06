import { useEffect, useState } from "react";
import { api } from "../api";
import type { LeaderboardEntry } from "../api";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getLeaderboard()
      .then(setEntries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 animate-fade-in-up space-y-3">
        <div className="h-8 w-40 skeleton rounded mb-6" />
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-12 skeleton rounded-xl" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-6 animate-fade-in-up">
        <div className="rounded-xl border border-[#23252a] bg-[#16181a] p-8 text-center">
          <p className="text-[#ef4444] text-sm font-medium">Failed to load leaderboard</p>
          <p className="text-[#62666d] text-xs mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 animate-fade-in-up">
      <h1 className="text-[22px] font-semibold text-[#f7f8f8] tracking-tight mb-6">Leaderboard</h1>

      {entries.length === 0 ? (
        <div className="rounded-xl border border-[#23252a] bg-[#16181a] p-10 text-center">
          <svg className="w-10 h-10 mx-auto mb-3 text-[#34343a]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 0 1 3 3h-15a3 3 0 0 1 3-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 0 1-.982-3.172M9.497 14.25a7.454 7.454 0 0 0 .981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 0 0 7.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M18.75 4.236c.982.143 1.954.317 2.916.52A6.003 6.003 0 0 1 16.27 9.728M18.75 4.236V4.5c0 2.108-.966 3.99-2.48 5.228m0 0a6.022 6.022 0 0 1-2.77 1.022" />
          </svg>
          <p className="text-[#8a8f98] text-sm font-medium">No predictions yet</p>
          <p className="text-[#62666d] text-xs mt-1">Be the first to place a prediction and top the leaderboard!</p>
        </div>
      ) : (
        <div className="rounded-xl border border-[#23252a] bg-[#0f1011] overflow-hidden">
          {/* Table header */}
          <div className="hidden sm:grid grid-cols-[48px_1fr_80px_80px_80px_64px_48px] gap-3 px-5 py-3 border-b border-[#23252a] text-[11px] font-semibold text-[#8a8f98] uppercase tracking-wider">
            <div>#</div>
            <div>Player</div>
            <div className="text-right">Wagered</div>
            <div className="text-right">Won</div>
            <div className="text-right">Win Rate</div>
            <div className="text-right">Picks</div>
            <div className="text-right">Streak</div>
          </div>

          {/* Table body */}
          {entries.map((e, i) => {
            const streak = e.predictions_count >= 3 && e.win_rate > 0.5 ? "🔥" : e.win_rate > 0.3 ? "📈" : "—";
            return (
            <div
              key={e.rank}
              className="grid grid-cols-[auto_1fr_auto] sm:grid-cols-[48px_1fr_80px_80px_80px_64px_48px] gap-2 sm:gap-3 px-4 sm:px-5 py-3 border-b border-[#23252a]/50 hover:bg-[rgba(255,255,255,0.01)] transition"
              style={{ animationDelay: `${i * 30}ms` }}
            >
              <div className="text-[#f7f8f8] font-bold text-sm">
                {e.rank <= 3 ? ["🥇", "🥈", "🥉"][e.rank - 1] : e.rank}
              </div>
              {/* Mobile: stacked info */}
              <div className="sm:hidden flex flex-col">
                <span className="text-[#d0d6e0] text-sm font-medium truncate font-mono">
                  {e.user_address.slice(0, 6)}...{e.user_address.slice(-4)}
                </span>
                <span className="text-[12px] text-[#62666d]">
                  {e.total_wagered.toFixed(1)} wagered &middot; {e.total_won.toFixed(1)} won &middot; {(e.win_rate * 100).toFixed(0)}% &middot; {e.predictions_count} picks
                </span>
              </div>
              {/* Desktop columns */}
              <div className="hidden sm:block text-[#d0d6e0] text-sm font-medium truncate font-mono tabular-nums">
                {e.user_address.slice(0, 8)}...{e.user_address.slice(-4)}
              </div>
              <div className="hidden sm:block text-right text-[#d0d6e0] text-sm tabular-nums">
                {e.total_wagered.toFixed(1)}
              </div>
              <div className="hidden sm:block text-right text-[#27a644] text-sm font-medium tabular-nums">
                {e.total_won.toFixed(1)}
              </div>
              <div className="hidden sm:block text-right text-[#f59e0b] text-sm tabular-nums">
                {(e.win_rate * 100).toFixed(1)}%
              </div>
              <div className="hidden sm:block text-right text-[#62666d] text-sm tabular-nums">
                {e.predictions_count}
              </div>
              <div className="text-right text-sm tabular-nums">
                {streak}
              </div>
            </div>
          )})}
        </div>
      )}
    </div>
  );
}
