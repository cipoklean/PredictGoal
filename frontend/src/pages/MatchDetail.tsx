import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import type { Match } from "../api";

const COUNTRY_FLAGS: Record<string, string> = {
  Argentina: "ar", Brazil: "br", Germany: "de", France: "fr",
  Spain: "es", England: "gb-eng", Japan: "jp", Nigeria: "ng",
  Mexico: "mx", "South Africa": "za", "South Korea": "kr", Czechia: "cz",
  Canada: "ca", "Bosnia-Herzegovina": "ba", "United States": "us",
  Paraguay: "py", Qatar: "qa", Switzerland: "ch", TBD: "",
};

function flagUrl(code: string): string {
  return code ? `https://flagcdn.com/w80/${code}.png` : "";
}

export default function MatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [match, setMatch] = useState<Match | null>(null);
  const [analytics, setAnalytics] = useState<{
    win_prob_home: number;
    win_prob_draw: number;
    win_prob_away: number;
    key_stats: Record<string, unknown>;
  } | null>(null);
  const [outcome, setOutcome] = useState("home");
  const [stake, setStake] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    Promise.all([api.getMatch(id), api.getMatchAnalytics(id)])
      .then(([m, a]) => {
        setMatch(m);
        setAnalytics(a);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const placePrediction = async () => {
    if (!id) return;
    setSubmitting(true);
    setMsg("");
    try {
      const result = await api.placePrediction({ match_id: id, outcome, stake_usdc: stake });
      setMsg(`Prediction placed: ${result.stake_usdc} USDC on ${result.outcome.toUpperCase()}`);
      setStake(1);
    } catch (e: unknown) {
      setMsg(`Error: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-6 animate-fade-in-up space-y-4">
        <div className="h-8 w-64 skeleton rounded" />
        <div className="h-32 skeleton rounded-xl" />
        <div className="h-40 skeleton rounded-xl" />
      </div>
    );
  }

  if (error || !match) {
    return (
      <div className="max-w-2xl mx-auto px-6 animate-fade-in-up">
        <div className="rounded-xl border border-[#23252a] bg-[#16181a] p-8 text-center">
          <p className="text-[#ef4444] text-sm font-medium">Match not found</p>
          <p className="text-[#62666d] text-xs mt-1">{error || "Invalid match ID"}</p>
        </div>
      </div>
    );
  }

  const homeFlag = COUNTRY_FLAGS[match.home_team] || "";
  const awayFlag = COUNTRY_FLAGS[match.away_team] || "";

  return (
    <div className="max-w-2xl mx-auto px-6 animate-fade-in-up space-y-6">
      {/* Match header */}
      <div className="rounded-xl border border-[#23252a] bg-[#0f1011] p-6 text-center">
        <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded mb-4 ${
          match.status === "live" ? "bg-[#ef4444]/10 text-[#ef4444]"
            : match.status === "finished" ? "bg-[#62666d]/10 text-[#62666d]"
            : "bg-[#5e6ad2]/10 text-[#7170ff]"
        }`}>
          {match.status === "live" && <span className="w-1.5 h-1.5 rounded-full bg-[#ef4444] animate-live inline-block" />}
          {match.status}
        </span>

        <div className="flex items-center justify-center gap-4 sm:gap-8">
          <div className="flex flex-col items-center gap-2">
            {homeFlag && <img src={flagUrl(homeFlag)} alt="" className="w-12 h-8 rounded" />}
            <span className="text-[#f7f8f8] text-lg font-semibold">{match.home_team}</span>
          </div>

          <div className="flex flex-col items-center">
            {match.home_score !== null && match.away_score !== null ? (
              <span className="text-4xl font-bold text-[#f7f8f8] tabular-nums tracking-tight">
                {match.home_score} <span className="text-[#8a8f98] font-normal">—</span> {match.away_score}
              </span>
            ) : (
              <span className="text-[#62666d] text-sm font-medium uppercase tracking-wider">vs</span>
            )}
            <span className="text-[11px] text-[#62666d] mt-2">
              {new Date(match.kickoff_utc).toLocaleDateString("en-US", {
                weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
              })}
            </span>
          </div>

          <div className="flex flex-col items-center gap-2">
            {awayFlag && <img src={flagUrl(awayFlag)} alt="" className="w-12 h-8 rounded" />}
            <span className="text-[#f7f8f8] text-lg font-semibold">{match.away_team}</span>
          </div>
        </div>
      </div>

      {/* Analytics */}
      {analytics && (
        <div className="rounded-xl border border-[#23252a] bg-[#0f1011] p-5">
          <h2 className="text-[13px] font-semibold text-[#8a8f98] uppercase tracking-wider mb-4">Win Probabilities</h2>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Home", prob: analytics.win_prob_home, color: "bg-[#27a644]", glow: "shadow-[0_0_12px_rgba(39,166,68,0.3)]" },
              { label: "Draw", prob: analytics.win_prob_draw, color: "bg-[#f59e0b]", glow: "shadow-[0_0_12px_rgba(245,158,11,0.3)]" },
              { label: "Away", prob: analytics.win_prob_away, color: "bg-[#3b82f6]", glow: "shadow-[0_0_12px_rgba(59,130,246,0.3)]" },
            ].map(({ label, prob, color, glow }) => {
              const maxProb = Math.max(
                analytics.win_prob_home,
                analytics.win_prob_draw,
                analytics.win_prob_away
              );
              const isFavored = prob === maxProb && maxProb > 0;
              return (
              <div
                key={label}
                className={`text-center rounded-lg p-2 transition-all duration-500 ${
                  isFavored ? `${glow} bg-[rgba(255,255,255,0.02)]` : ""
                }`}
              >
                <div className="text-[11px] text-[#8a8f98] font-medium mb-1.5 uppercase tracking-wider">
                  {label}{isFavored && " ☆"}
                </div>
                <div className={`text-2xl font-bold tabular-nums transition-colors duration-500 ${
                  isFavored ? "text-[#f7f8f8]" : "text-[#d0d6e0]"
                }`}>
                  {(prob * 100).toFixed(1)}%
                </div>
                <div className="mt-2 h-1.5 rounded-full bg-[#23252a] overflow-hidden">
                  <div
                    className={`h-full rounded-full ${color} transition-all duration-500 ${
                      isFavored ? "animate-pulse" : ""
                    }`}
                    style={{ width: `${prob * 100}%` }}
                  />
                </div>
              </div>
            )})}
          </div>
          {analytics.key_stats && (
            <div className="mt-4 pt-4 border-t border-[#23252a] grid grid-cols-2 gap-2 text-[12px]">
              {Object.entries(analytics.key_stats).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-[#62666d] capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="text-[#d0d6e0] font-medium">{String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Place prediction */}
      {match.status !== "finished" && (
        <div className="rounded-xl border border-[#23252a] bg-[#0f1011] p-5">
          <h2 className="text-[13px] font-semibold text-[#8a8f98] uppercase tracking-wider mb-4">Place Prediction</h2>

          {/* Outcome selector */}
          <div className="flex gap-1.5 mb-4">
            {(["home", "draw", "away"] as const).map((o, i) => (
              <button
                key={o}
                onClick={() => setOutcome(o)}
                className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 uppercase tracking-wider ${
                  outcome === o
                    ? "bg-[#5e6ad2] text-white"
                    : "bg-[rgba(255,255,255,0.03)] text-[#8a8f98] hover:bg-[rgba(255,255,255,0.06)] hover:text-[#d0d6e0] border border-[#23252a]"
                }`}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                {o}
              </button>
            ))}
          </div>

          {/* Stake input */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="number"
                min={0.1}
                max={100}
                step={0.1}
                value={stake}
                onChange={(e) => setStake(parseFloat(e.target.value) || 0)}
                className="w-full rounded-lg bg-[rgba(255,255,255,0.03)] border border-[#23252a] px-4 py-2.5 text-[#f7f8f8] text-sm font-medium outline-none focus:border-[#5e6ad2] focus:ring-1 focus:ring-[#5e6ad2]/20 transition-all duration-200"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[#62666d] text-xs font-medium">USDC</span>
            </div>
            <button
              onClick={placePrediction}
              disabled={submitting || stake <= 0}
              className="bg-[#5e6ad2] hover:bg-[#7170ff] disabled:bg-[#23252a] disabled:text-[#62666d] text-white text-sm font-semibold px-6 rounded-lg transition-all duration-200 active:scale-[0.97]"
            >
              {submitting ? "Placing..." : "Predict"}
            </button>
          </div>

          {/* Message */}
          {msg && (
            <div className={`mt-3 text-[12px] font-medium rounded-lg px-3 py-2 ${
              msg.startsWith("Error")
                ? "bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/20"
                : "bg-[#27a644]/10 text-[#27a644] border border-[#27a644]/20"
            }`}>
              {msg}
            </div>
          )}
        </div>
      )}

      {/* Faucet hint */}
      <div className="rounded-lg bg-[rgba(94,106,210,0.05)] border border-[#5e6ad2]/15 p-3 text-center">
        <p className="text-[11px] text-[#8a8f98]">
          Need testnet USDC? Grab some from{" "}
          <a href="https://testnet.faucet.injective.network" target="_blank" className="text-[#7170ff] hover:text-[#828fff] font-medium transition">
            Injective Testnet Faucet
          </a>
          {" "}&middot; Micro-stakes only &middot; Zero real funds
        </p>
      </div>
    </div>
  );
}
