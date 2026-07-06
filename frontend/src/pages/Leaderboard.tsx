import { useEffect, useState } from "react";
import { api } from "../api";
import type { LeaderboardEntry } from "../api";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { api.getLeaderboard().then(setEntries).catch((e) => setError(e.message)).finally(() => setLoading(false)); }, []);

  if (loading) return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 animate-fade-in-up space-y-3">
      <div className="h-10 w-44 skeleton rounded-lg mb-6" />
      {Array.from({ length: 3 }).map((_, i) => (<div key={i} className="h-16 skeleton rounded-2xl" />))}
    </div>
  );

  if (error) return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 animate-fade-in-up">
      <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-10 text-center">
        <p className="text-[#ea2261] text-sm font-semibold">Failed to load leaderboard</p>
        <p className="text-[#4d5063] text-xs mt-1.5">{error}</p>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 animate-fade-in-up">
      <h1 className="text-2xl font-bold text-[#e8eaf0] tracking-tight mb-6">Leaderboard</h1>

      {entries.length === 0 ? (
        <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-12 text-center">
          <svg className="w-12 h-12 mx-auto mb-4 text-[#1e2140]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728" />
          </svg>
          <p className="text-[#7b7f92] text-sm font-semibold">No predictions yet</p>
          <p className="text-[#4d5063] text-xs mt-1">Be the first to place a prediction and top the leaderboard!</p>
        </div>
      ) : (
        <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] overflow-hidden">
          {/* Header */}
          <div className="hidden sm:grid grid-cols-[56px_1fr_90px_90px_90px_72px_56px] gap-3 px-6 py-4 border-b border-[rgba(83,58,253,0.08)] text-xs font-bold text-[#7b7f92] uppercase tracking-widest">
            <div>#</div><div>Player</div><div className="text-right">Wagered</div>
            <div className="text-right">Won</div><div className="text-right">Win Rate</div>
            <div className="text-right">Picks</div><div className="text-right">Streak</div>
          </div>

          {entries.map((e, i) => {
            const isTop3 = e.rank <= 3;
            const streak = e.predictions_count >= 3 && e.win_rate > 0.5 ? "🔥" : e.win_rate > 0.3 ? "📈" : "—";
            return (
              <div key={e.rank}
                className={`grid grid-cols-[auto_1fr_auto] sm:grid-cols-[56px_1fr_90px_90px_90px_72px_56px] gap-2 sm:gap-3 px-4 sm:px-6 py-4 border-b border-[rgba(83,58,253,0.04)] transition hover:bg-[rgba(83,58,253,0.02)] ${
                  isTop3 ? "bg-[rgba(83,58,253,0.03)]" : ""
                }`}
                style={{ animationDelay: `${i * 30}ms` }}>
                <div className={`text-sm font-bold tabular-nums ${
                  e.rank === 1 ? "text-[#e5a00d]" : e.rank === 2 ? "text-[#7b7f92]" : e.rank === 3 ? "text-[#a0522d]" : "text-[#4d5063]"
                }`}>
                  {isTop3 ? ["🥇", "🥈", "🥉"][e.rank - 1] : e.rank}
                </div>

                {/* Mobile stacked */}
                <div className="sm:hidden flex flex-col">
                  <span className="text-sm font-semibold text-[#e8eaf0] truncate font-mono">{e.user_address.slice(0, 6)}...{e.user_address.slice(-4)}</span>
                  <span className="text-[11px] text-[#4d5063]">{e.total_wagered.toFixed(1)} wagered &middot; {e.total_won.toFixed(1)} won &middot; {(e.win_rate * 100).toFixed(0)}% &middot; {e.predictions_count} picks</span>
                </div>

                {/* Desktop columns */}
                <div className="hidden sm:block text-sm font-semibold text-[#e8eaf0] truncate font-mono tabular-nums">{e.user_address.slice(0, 8)}...{e.user_address.slice(-4)}</div>
                <div className="hidden sm:block text-right text-sm text-[#e8eaf0] tabular-nums font-mono">{e.total_wagered.toFixed(1)}</div>
                <div className="hidden sm:block text-right text-sm font-bold text-[#15be53] tabular-nums font-mono">{e.total_won.toFixed(1)}</div>
                <div className="hidden sm:block text-right text-sm font-bold text-[#e5a00d] tabular-nums font-mono">{(e.win_rate * 100).toFixed(1)}%</div>
                <div className="hidden sm:block text-right text-sm text-[#7b7f92] tabular-nums">{e.predictions_count}</div>
                <div className="text-right text-sm">{streak}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
