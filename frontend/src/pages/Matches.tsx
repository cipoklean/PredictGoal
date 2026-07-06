import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Match } from "../api";

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getMatches()
      .then((res) => setMatches(res.matches))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center p-8 text-gray-400">Loading matches...</div>;
  if (error) return <div className="text-center p-8 text-red-500">Error: {error}</div>;

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-white">World Cup Matches</h1>
      <div className="grid gap-4">
        {matches.map((m) => (
          <Link
            key={m.match_id}
            to={`/matches/${m.match_id}`}
            className="block bg-gray-800 hover:bg-gray-750 rounded-lg p-4 transition border border-gray-700"
          >
            <div className="flex justify-between items-center">
              <div>
                <span className="font-semibold text-white">{m.home_team}</span>
                <span className="mx-2 text-gray-500">vs</span>
                <span className="font-semibold text-white">{m.away_team}</span>
              </div>
              <span
                className={`text-xs px-2 py-1 rounded ${
                  m.status === "live"
                    ? "bg-green-600 text-white animate-pulse"
                    : m.status === "finished"
                    ? "bg-gray-600 text-gray-300"
                    : "bg-blue-600 text-white"
                }`}
              >
                {m.status.toUpperCase()}
              </span>
            </div>
            {m.home_score !== null && m.away_score !== null && (
              <div className="mt-2 text-2xl font-bold text-white">
                {m.home_score} - {m.away_score}
              </div>
            )}
            <div className="mt-2 text-xs text-gray-500">
              {new Date(m.kickoff_utc).toLocaleString()}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
