import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import type { Match } from "../api";

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

  useEffect(() => {
    if (!id) return;
    Promise.all([api.getMatch(id), api.getMatchAnalytics(id)])
      .then(([m, a]) => {
        setMatch(m);
        setAnalytics(a);
      })
      .finally(() => setLoading(false));
  }, [id]);

  const placePrediction = async () => {
    if (!id) return;
    setSubmitting(true);
    setMsg("");
    try {
      const result = await api.placePrediction({
        match_id: id,
        outcome,
        stake_usdc: stake,
      });
      setMsg(`Prediction placed! ${result.stake_usdc} USDC on ${result.outcome}`);
      setStake(1);
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="text-center p-8 text-gray-400">Loading...</div>;
  if (!match) return <div className="text-center p-8 text-red-500">Match not found</div>;

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-3xl font-bold text-white">
        {match.home_team} vs {match.away_team}
      </h1>
      <p className="text-gray-400 mt-1">
        {new Date(match.kickoff_utc).toLocaleString()} —{" "}
        <span
          className={
            match.status === "live" ? "text-green-400" : match.status === "finished" ? "text-gray-500" : "text-blue-400"
          }
        >
          {match.status.toUpperCase()}
        </span>
      </p>

      {match.home_score !== null && (
        <div className="mt-4 text-4xl font-bold text-white text-center">
          {match.home_score} — {match.away_score}
        </div>
      )}

      {analytics && (
        <div className="mt-6 bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">AI Win Probabilities</h2>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">Home</div>
              <div className="text-xl font-bold text-green-400">
                {(analytics.win_prob_home * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">Draw</div>
              <div className="text-xl font-bold text-yellow-400">
                {(analytics.win_prob_draw * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">Away</div>
              <div className="text-xl font-bold text-blue-400">
                {(analytics.win_prob_away * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {match.status !== "finished" && (
        <div className="mt-6 bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">Place Prediction</h2>
          <div className="flex gap-2 mb-4">
            {(["home", "draw", "away"] as const).map((o) => (
              <button
                key={o}
                onClick={() => setOutcome(o)}
                className={`flex-1 py-2 rounded font-semibold transition ${
                  outcome === o
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                {o.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="number"
              min={0.1}
              max={100}
              step={0.1}
              value={stake}
              onChange={(e) => setStake(parseFloat(e.target.value) || 0)}
              className="flex-1 bg-gray-700 rounded px-3 py-2 text-white border border-gray-600"
            />
            <button
              onClick={placePrediction}
              disabled={submitting || stake <= 0}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-600 text-white px-6 py-2 rounded font-semibold transition"
            >
              {submitting ? "Placing..." : "Predict"}
            </button>
          </div>
          {msg && (
            <div className={`mt-3 text-sm ${msg.startsWith("Error") ? "text-red-400" : "text-green-400"}`}>{msg}</div>
          )}
        </div>
      )}
    </div>
  );
}
