import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import type { Match } from "../api";
import { isPaymentConnected } from "../x402Client";
import ConnectPayment from "../components/ConnectPayment";

type PremiumInsight = Awaited<ReturnType<typeof api.getPremiumInsight>>;

const COUNTRY_FLAGS: Record<string, string> = {
  Argentina: "ar", Brazil: "br", Germany: "de", France: "fr",
  Spain: "es", England: "gb-eng", Japan: "jp", Nigeria: "ng",
  Mexico: "mx", "South Africa": "za", "South Korea": "kr", Czechia: "cz",
  Canada: "ca", "Bosnia-Herzegovina": "ba", "United States": "us",
  Paraguay: "py", Qatar: "qa", Switzerland: "ch", TBD: "",
};

export default function MatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [match, setMatch] = useState<Match | null>(null);
  const [analytics, setAnalytics] = useState<{
    win_prob_home: number; win_prob_draw: number; win_prob_away: number;
    key_stats: Record<string, unknown>;
  } | null>(null);
  const [outcome, setOutcome] = useState("home");
  const [stake, setStake] = useState("1");
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"success" | "error">("success");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Premium insights (x402-gated)
  const [insight, setInsight] = useState<PremiumInsight | null>(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [insightError, setInsightError] = useState("");
  // x402 dev-mode note shown briefly while "unlocking" (passthrough demo).
  const [x402Note, setX402Note] = useState("");
  // Bumps when the x402 payment wallet connects/disconnects, so isPaymentConnected() re-evaluates.
  const [, bumpPayment] = useState(0);

  useEffect(() => {
    if (!id) return;
    Promise.all([api.getMatch(id), api.getMatchAnalytics(id)])
      .then(([m, a]) => { setMatch(m); setAnalytics(a); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const placePrediction = async () => {
    if (!id) return;
    const stakeNum = parseFloat(stake) || 0;
    if (stakeNum <= 0) return;
    setSubmitting(true); setMsg("");
    try {
      const result = await api.placePrediction({ match_id: id, outcome, stake_usdc: stakeNum });
      setMsgType("success");
      setMsg(`Prediction placed! ${result.stake_usdc} USDC on ${result.outcome.toUpperCase()}`);
      setStake("1");
    } catch (e: unknown) {
      setMsgType("error");
      setMsg(e instanceof Error ? e.message : "Unknown error");
    } finally { setSubmitting(false); }
  };

  const loadInsight = async () => {
    if (!id) return;
    setLoadingInsight(true); setInsightError("");
    // Clearly-labeled x402 dev-mode pause so the pay-per-use flow is visible.
    // In passthrough (hackathon demo) no real USDC is charged.
    setX402Note("⚡ x402 · dev mode — 3.0 USDC on Injective EVM testnet (no real charge)");
    try {
      await new Promise((r) => setTimeout(r, 900));
      const data = await api.getPremiumInsight(id);
      setInsight(data);
    } catch (e: unknown) {
      setInsightError(e instanceof Error ? e.message : "Failed to load insight");
    } finally { setLoadingInsight(false); setX402Note(""); }
  };

  if (loading) return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 animate-fade-in-up space-y-4">
      <div className="h-10 w-64 skeleton rounded-lg" />
      <div className="h-44 skeleton rounded-2xl" />
      <div className="h-52 skeleton rounded-2xl" />
    </div>
  );

  if (error || !match) return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 animate-fade-in-up">
      <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-10 text-center">
        <p className="text-[#ea2261] text-sm font-semibold">Match not found</p>
        <p className="text-[#7b7f92] text-xs mt-1.5">{error || "Invalid match ID"}</p>
      </div>
    </div>
  );

  const homeFlag = COUNTRY_FLAGS[match.home_team] || "";
  const awayFlag = COUNTRY_FLAGS[match.away_team] || "";
  const isLive = match.status === "live";
  const isFinished = match.status === "finished";

  // Find favored outcome
  const probs = analytics ? [
    { label: "Home", prob: analytics.win_prob_home },
    { label: "Draw", prob: analytics.win_prob_draw },
    { label: "Away", prob: analytics.win_prob_away },
  ] : [];
  const maxProb = Math.max(...probs.map((p) => p.prob), 0);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 animate-fade-in-up space-y-5">
      {/* Match header card */}
      <div className="rounded-2xl border border-[rgba(83,58,253,0.12)] bg-gradient-to-b from-[#11131f] to-[#161929] p-6 sm:p-8 text-center relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-32 bg-[radial-gradient(ellipse_at_center,rgba(83,58,253,0.12)_0%,transparent_70%)] pointer-events-none" />

        <span className={`relative inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full mb-5 ${
          isLive ? "bg-[rgba(234,34,97,0.12)] text-[#ea2261] border border-[rgba(234,34,97,0.2)]" :
          isFinished ? "bg-[rgba(77,80,99,0.2)] text-[#7b7f92] border border-[rgba(77,80,99,0.2)]" :
          "bg-[rgba(83,58,253,0.12)] text-[#a89ffa] border border-[rgba(83,58,253,0.2)]"
        }`}>
          {isLive && <span className="w-2 h-2 rounded-full bg-[#ea2261] animate-[live-dot_1.5s_infinite]" />}
          {match.status}
        </span>

        <div className="relative flex items-center justify-center gap-4 sm:gap-10">
          <div className="flex flex-col items-center gap-3">
            {homeFlag && <img src={`https://flagcdn.com/w80/${homeFlag}.png`} alt="" className="w-14 h-10 rounded shadow-lg" />}
            <span className="text-[#e8eaf0] text-lg sm:text-xl font-bold">{match.home_team}</span>
          </div>

          <div className="flex flex-col items-center">
            {match.home_score !== null && match.away_score !== null ? (
              <span className="text-5xl sm:text-6xl font-bold text-[#e8eaf0] tabular-nums tracking-tight">
                {match.home_score}
                <span className="text-[#4d5063] font-light mx-1.5">—</span>
                {match.away_score}
              </span>
            ) : (
              <span className="text-[#4d5063] text-sm font-semibold uppercase tracking-widest">vs</span>
            )}
            <span className="text-xs text-[#7b7f92] mt-2 font-medium">
              {new Date(match.kickoff_utc).toLocaleDateString("en-US", {
                weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
              })}
            </span>
          </div>

          <div className="flex flex-col items-center gap-3">
            {awayFlag && <img src={`https://flagcdn.com/w80/${awayFlag}.png`} alt="" className="w-14 h-10 rounded shadow-lg" />}
            <span className="text-[#e8eaf0] text-lg sm:text-xl font-bold">{match.away_team}</span>
          </div>
        </div>
      </div>

      {/* Win probabilities */}
      {analytics && (
        <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-5 sm:p-6">
          <h2 className="text-xs font-semibold text-[#7b7f92] uppercase tracking-widest mb-5">Win Probabilities</h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Home", prob: analytics.win_prob_home, gradient: "from-[#15be53] to-[#0dd85f]", glow: "rgba(21,190,83,0.3)" },
              { label: "Draw", prob: analytics.win_prob_draw, gradient: "from-[#e5a00d] to-[#f5b014]", glow: "rgba(229,160,13,0.3)" },
              { label: "Away", prob: analytics.win_prob_away, gradient: "from-[#3b82f6] to-[#60a5fa]", glow: "rgba(59,130,246,0.3)" },
            ].map(({ label, prob, gradient, glow }) => {
              const isFavored = prob === maxProb && maxProb > 0;
              return (
                <div
                  key={label}
                  className="text-center transition-all duration-500"
                  style={isFavored ? { filter: `drop-shadow(0_0_12px_${glow})` } : undefined}
                >
                  <div className="text-[11px] text-[#7b7f92] font-semibold uppercase tracking-widest mb-2">
                    {label}{isFavored && " ☆"}
                  </div>
                  <div className={`text-2xl sm:text-3xl font-bold tabular-nums transition-colors duration-500 ${
                    isFavored ? "text-white" : "text-[#7b7f92]"
                  }`}>
                    {(prob * 100).toFixed(1)}%
                  </div>
                  <div className="mt-2.5 h-2 rounded-full bg-[#1e2140] overflow-hidden">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${gradient} transition-all duration-700 ease-out ${
                        isFavored ? "animate-pulse" : ""
                      }`}
                      style={{ width: `${Math.max(prob * 100, 2)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {analytics.key_stats && (
            <div className="mt-5 pt-4 border-t border-[rgba(83,58,253,0.08)] grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs">
              {Object.entries(analytics.key_stats).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-[#4d5063] capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="text-[#a89ffa] font-semibold font-mono">{String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Premium Insights */}
      <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-5 sm:p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xs font-semibold text-[#7b7f92] uppercase tracking-widest">Premium Insights</h2>
          {insight && (
            <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full ${
              insight.data_source === "football-data"
                ? "bg-[rgba(21,190,83,0.12)] text-[#15be53] border border-[rgba(21,190,83,0.25)]"
                : "bg-[rgba(229,160,13,0.12)] text-[#e5a00d] border border-[rgba(229,160,13,0.25)]"
            }`}>
              {insight.data_source === "football-data" ? "● LIVE · football-data" : "● SIMULATED"}
            </span>
          )}
        </div>

        {!insight ? (
          <div className="text-center py-2">
            <p className="text-[#7b7f92] text-xs mb-4">
              Momentum, real form, head-to-head &amp; top scorers — pay-per-use via x402.
            </p>
            {isPaymentConnected() ? (
              <button
                onClick={loadInsight}
                disabled={loadingInsight}
                className="bg-gradient-to-br from-[#533afd] to-[#7b6ff0] hover:from-[#4434d4] hover:to-[#6b5fe0] disabled:from-[#1e2140] disabled:to-[#1e2140] disabled:text-[#4d5063] text-white text-sm font-bold px-6 py-3 rounded-xl transition-all duration-200 active:scale-[0.97] shadow-[0_0_20px_rgba(83,58,253,0.25)] hover:shadow-[0_0_28px_rgba(83,58,253,0.4)]"
              >
                {loadingInsight ? "Unlocking..." : "⚡ Unlock Premium Insight — 3.0 USDC"}
              </button>
            ) : (
              <ConnectPayment
                label="Connect Wallet to Unlock (3.0 USDC)"
                hint="Connect MetaMask (Injective EVM testnet) to pay 3.0 USDC when you unlock. Connecting does not charge anything."
                onConnected={() => bumpPayment((x) => x + 1)}
              />
            )}
            {x402Note && (
              <p className="mt-3 text-[11px] text-[#a89ffa] font-medium flex items-center justify-center gap-1.5">
                <span className="animate-pulse">⚡</span>{x402Note}
              </p>
            )}
            {insightError && (
              <p className="mt-3 text-[11px] text-[#ea2261] font-semibold">{insightError}</p>
            )}
            <p className="mt-3 text-[10px] text-[#4d5063]">
              x402 pay-per-use · dev-mode passthrough (zero real funds)
            </p>
            </div>
        ) : (
          <div className="space-y-5 animate-fade-in-up">
            <div>
              <p className="text-[11px] text-[#4d5063] uppercase tracking-widest mb-2">Momentum</p>
              <div className="space-y-2">
                <InsightBar label={match.home_team} value={Number(insight.momentum.home_momentum)} color="from-[#15be53] to-[#0dd85f]" />
                <InsightBar label={match.away_team} value={Number(insight.momentum.away_momentum)} color="from-[#3b82f6] to-[#60a5fa]" />
              </div>
              <p className="mt-2 text-[11px] text-[#7b7f92]">
                Score pressure: <span className="text-[#a89ffa] font-semibold">{String(insight.momentum.score_pressure)}</span>
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(83,58,253,0.08)] p-3">
                <p className="text-[10px] text-[#4d5063] uppercase tracking-widest mb-1 truncate">{match.home_team}</p>
                <p className="text-sm font-bold font-mono text-[#e8eaf0]">{String(insight.form_analysis.home_form)}</p>
              </div>
              <div className="rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(83,58,253,0.08)] p-3 text-center">
                <p className="text-[10px] text-[#4d5063] uppercase tracking-widest mb-1">H2H</p>
                <p className="text-sm font-bold font-mono text-[#e8eaf0]">{String(insight.form_analysis.head_to_head)}</p>
              </div>
              <div className="rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(83,58,253,0.08)] p-3 text-right">
                <p className="text-[10px] text-[#4d5063] uppercase tracking-widest mb-1 truncate">{match.away_team}</p>
                <p className="text-sm font-bold font-mono text-[#e8eaf0]">{String(insight.form_analysis.away_form)}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-[rgba(21,190,83,0.05)] border border-[rgba(21,190,83,0.12)] p-3">
                <p className="text-[10px] text-[#4d5063] uppercase tracking-widest mb-1">{match.home_team} key player</p>
                <p className="text-xs font-semibold text-[#e8eaf0]">{String(insight.key_player_impact.home_star)}</p>
              </div>
              <div className="rounded-xl bg-[rgba(59,130,246,0.05)] border border-[rgba(59,130,246,0.12)] p-3">
                <p className="text-[10px] text-[#4d5063] uppercase tracking-widest mb-1">{match.away_team} key player</p>
                <p className="text-xs font-semibold text-[#e8eaf0]">{String(insight.key_player_impact.away_star)}</p>
              </div>
            </div>

            <p className="text-[10px] text-[#4d5063] leading-relaxed">{insight.disclaimer}</p>

            <div className="mt-2 inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-[rgba(83,58,253,0.1)] text-[#a89ffa] border border-[rgba(83,58,253,0.2)]">
              <span>⚡</span> x402 {insight.x402_mode === "enforce" ? "· live payment" : "· dev-mode passthrough — no charge"}
            </div>

            <button
              onClick={() => { setInsight(null); setInsightError(""); }}
              className="text-[11px] text-[#7b7f92] hover:text-[#a89ffa] underline underline-offset-2 transition"
            >
              Reset
            </button>
          </div>
        )}
      </div>

      {/* Place prediction */}
      {!isFinished && (
        <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-5 sm:p-6">
          <h2 className="text-xs font-semibold text-[#7b7f92] uppercase tracking-widest mb-5">Place Prediction</h2>

          {!isPaymentConnected() && (
            <div className="mb-5 rounded-xl bg-[rgba(245,166,35,0.04)] border border-[rgba(245,166,35,0.12)] p-4">
              <ConnectPayment
                label="Connect Wallet to Predict (2.0 USDC)"
                hint="Connect MetaMask (Injective EVM testnet) to pay the 2.0 USDC platform fee when you place a prediction. Connecting does not charge anything."
                onConnected={() => bumpPayment((x) => x + 1)}
              />
            </div>
          )}
          {isPaymentConnected() && (
            <div className="mb-4 flex items-center gap-1.5 text-[11px]">
              <span className="text-[#f5a623] font-bold">⚡ Payments connected</span>
              <span className="text-[#7b7f92]">— 2.0 USDC fee is charged only when you Predict.</span>
            </div>
          )}

          {/* Outcome selector */}
          <div className="flex gap-2 mb-5">
            {([
              { key: "home", label: "Home", color: "hover:border-[#15be53]/40 data-[active]:bg-[rgba(21,190,83,0.15)] data-[active]:border-[#15be53]/40 data-[active]:text-[#15be53]" },
              { key: "draw", label: "Draw", color: "hover:border-[#e5a00d]/40 data-[active]:bg-[rgba(229,160,13,0.15)] data-[active]:border-[#e5a00d]/40 data-[active]:text-[#e5a00d]" },
              { key: "away", label: "Away", color: "hover:border-[#3b82f6]/40 data-[active]:bg-[rgba(59,130,246,0.15)] data-[active]:border-[#3b82f6]/40 data-[active]:text-[#3b82f6]" },
            ] as const).map(({ key, label, color }) => (
              <button
                key={key}
                onClick={() => setOutcome(key)}
                data-active={outcome === key ? "" : undefined}
                className={`flex-1 py-3 rounded-xl text-sm font-bold uppercase tracking-wider border border-[rgba(83,58,253,0.1)] text-[#7b7f92] transition-all duration-200 ${color}`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Stake */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="text" inputMode="decimal"
                placeholder="0"
                value={stake}
                onChange={(e) => {
                  const v = e.target.value;
                  // Allow empty, digits, and single decimal point
                  if (v === "" || /^\d*\.?\d*$/.test(v)) setStake(v);
                }}
                className="w-full rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(83,58,253,0.12)] px-4 py-3 text-sm font-semibold text-[#e8eaf0] outline-none focus:border-[#533afd] focus:ring-2 focus:ring-[#533afd]/20 transition-all duration-200 placeholder:text-[#4d5063]"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-[#4d5063]">USDC</span>
            </div>
            <button
              onClick={placePrediction}
              disabled={submitting || !isPaymentConnected() || isNaN(parseFloat(stake)) || parseFloat(stake) <= 0}
              className="bg-gradient-to-br from-[#533afd] to-[#7b6ff0] hover:from-[#4434d4] hover:to-[#6b5fe0] disabled:from-[#1e2140] disabled:to-[#1e2140] disabled:text-[#4d5063] text-white text-sm font-bold px-6 rounded-xl transition-all duration-200 active:scale-[0.97] shadow-[0_0_20px_rgba(83,58,253,0.25)] hover:shadow-[0_0_28px_rgba(83,58,253,0.4)]"
            >
              {submitting ? "Placing..." : "Predict"}
            </button>
          </div>

          {/* Potential payout */}
          {analytics && !isNaN(parseFloat(stake)) && parseFloat(stake) > 0 && (
            <div className="mt-4 space-y-2">
              <div className="rounded-xl bg-[rgba(21,190,83,0.05)] border border-[rgba(21,190,83,0.12)] px-4 py-3 flex items-center justify-between">
                <span className="text-xs font-bold text-[#7b7f92] uppercase tracking-widest">Potential Win</span>
                <span className="text-sm font-bold text-[#15be53] font-mono tabular-nums">
                  +{parseFloat(stake).toFixed(1)} USDC
                  <span className="text-[10px] text-[#7b7f92] ml-1.5 font-normal">(2x payout on correct prediction)</span>
                </span>
              </div>
              <div className="flex items-center justify-between px-1">
                <span className="text-[11px] text-[#4d5063] flex items-center gap-1">
                  Stake {parseFloat(stake).toFixed(1)} USDC
                </span>
                <span className="text-[11px] text-[#4d5063] flex items-center gap-1">
                  + 2.0 USDC platform fee
                </span>
                <span className="text-[11px] font-semibold text-[#e8eaf0]">
                  Total: {(parseFloat(stake) + 2.0).toFixed(1)} USDC
                </span>
              </div>
            </div>
          )}

          {msg && (
            <div className={`mt-4 text-xs font-semibold rounded-xl px-4 py-2.5 animate-fade-in-up ${
              msgType === "error"
                ? "bg-[rgba(234,34,97,0.1)] text-[#ea2261] border border-[rgba(234,34,97,0.2)]"
                : "bg-[rgba(21,190,83,0.1)] text-[#15be53] border border-[rgba(21,190,83,0.2)]"
            }`}>
              {msg}
            </div>
          )}
        </div>
      )}

      {/* Faucet hint */}
      <div className="rounded-xl bg-[rgba(83,58,253,0.04)] border border-[rgba(83,58,253,0.1)] p-3.5 text-center">
        <p className="text-xs text-[#7b7f92]">
          Need testnet USDC?{" "}
          <a href="https://testnet.faucet.injective.network" target="_blank" className="text-[#a89ffa] hover:text-[#c4bbff] font-semibold transition underline underline-offset-2">
            Injective Testnet Faucet
          </a>
          {" "}&middot; Micro-stakes only &middot; Zero real funds
        </p>
      </div>
    </div>
  );
}

function InsightBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.max(2, Math.min(100, value));
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-[#7b7f92] w-20 truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-[#1e2140] overflow-hidden">
        <div className={`h-full rounded-full bg-gradient-to-r ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-[#e8eaf0] w-8 text-right tabular-nums">{value.toFixed(0)}</span>
    </div>
  );
}
