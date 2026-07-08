import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Match, Prediction } from "../api";

const COUNTRY_FLAGS: Record<string, string> = {
  Argentina: "ar", Brazil: "br", Germany: "de", France: "fr",
  Spain: "es", England: "gb-eng", Japan: "jp", Nigeria: "ng",
  Mexico: "mx", "South Africa": "za", "South Korea": "kr", Czechia: "cz",
  Canada: "ca", "Bosnia-Herzegovina": "ba", "United States": "us",
  Paraguay: "py", Qatar: "qa", Switzerland: "ch", Italy: "it",
  Netherlands: "nl", Portugal: "pt", Belgium: "be", Croatia: "hr",
  Senegal: "sn", Uruguay: "uy", Denmark: "dk", Australia: "au",
  Morocco: "ma", Ghana: "gh", Cameroon: "cm", Ecuador: "ec",
  "Saudi Arabia": "sa", Tunisia: "tn", Poland: "pl", Serbia: "rs",
  Sweden: "se", Norway: "no", Austria: "at", Egypt: "eg",
  Algeria: "dz", "Ivory Coast": "ci", Colombia: "co", Chile: "cl",
  Peru: "pe", Turkey: "tr", Ukraine: "ua", Romania: "ro",
  Scotland: "gb-sct", Wales: "gb-wls", Hungary: "hu", Slovakia: "sk",
  Greece: "gr", "New Zealand": "nz", "Costa Rica": "cr", Panama: "pa",
  Mali: "ml", "Burkina Faso": "bf", "DR Congo": "cd", Zambia: "zm",
  TBD: "",
};

function flagUrl(code: string): string {
  return code ? `https://flagcdn.com/w40/${code}.png` : "";
}

function getCountdown(utc: string): string {
  const diff = new Date(utc).getTime() - Date.now();
  if (diff <= 0) return "Kickoff";
  const d = Math.floor(diff / 86400000);
  const h = Math.floor((diff % 86400000) / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

type Filter = "all" | "live" | "upcoming" | "finished" | "mybets";

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [, setTick] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Fetch matches independently — don't let auth errors block the page
    api.getMatches()
      .then((res) => setMatches(res.matches))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

    // My predictions — silently ignore if not authenticated
    api.getMyPredictions()
      .then(setPredictions)
      .catch(() => setPredictions([]));
  }, []);

  const filtered = matches
    .filter((m) => {
      if (filter === "all") return true;
      if (filter === "live") return m.status === "live";
      if (filter === "upcoming") return m.status === "scheduled";
      if (filter === "finished") return m.status === "finished";
      return true;
    })
    .sort((a, b) => new Date(b.kickoff_utc).getTime() - new Date(a.kickoff_utc).getTime());

  if (loading) return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 animate-fade-in-up space-y-3">
      <div className="h-10 w-48 skeleton rounded-lg mb-6" />
      {Array.from({ length: 5 }).map((_, i) => (<div key={i} className="h-24 skeleton rounded-2xl" />))}
    </div>
  );

  if (error) return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 animate-fade-in-up">
      <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-10 text-center">
        <p className="text-[#ea2261] text-sm font-semibold">Failed to load matches</p>
        <p className="text-[#4d5063] text-xs mt-1.5">{error}</p>
      </div>
    </div>
  );

  const counts = {
    all: matches.length,
    live: matches.filter((m) => m.status === "live").length,
    upcoming: matches.filter((m) => m.status === "scheduled").length,
    finished: matches.filter((m) => m.status === "finished").length,
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 animate-fade-in-up">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[#e8eaf0] tracking-tight">Matches</h1>
        <span className="text-sm text-[#7b7f92] font-medium">
          {counts.live} live &middot; {counts.upcoming} upcoming
        </span>
      </div>

      {/* Filter pills */}
      <div className="flex gap-1.5 mb-6 overflow-x-auto pb-1">
        {(["all", "live", "upcoming", "finished"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3.5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 capitalize whitespace-nowrap ${
              filter === f
                ? "bg-[rgba(83,58,253,0.15)] text-[#a89ffa] border border-[rgba(83,58,253,0.25)]"
                : "text-[#7b7f92] hover:text-[#e8eaf0] hover:bg-[rgba(255,255,255,0.03)] border border-transparent"
            }`}
          >
            {f} <span className="ml-1.5 text-[#4d5063]">{counts[f]}</span>
          </button>
        ))}
        {predictions.length > 0 && (
          <button
            onClick={() => setFilter("mybets")}
            className={`px-3.5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 whitespace-nowrap ${
              filter === "mybets"
                ? "bg-[rgba(83,58,253,0.2)] text-[#c4bbff] border border-[rgba(83,58,253,0.35)]"
                : "text-[#a89ffa] hover:text-[#c4bbff] hover:bg-[rgba(83,58,253,0.06)] border border-transparent"
            }`}
          >
            My Bets <span className="ml-1.5">{predictions.length}</span>
          </button>
        )}
      </div>

      {/* My Bets */}
      {filter === "mybets" && (
        <div className="space-y-3">
          {predictions.length === 0 ? (
            <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-10 text-center">
              <p className="text-[#7b7f92] text-sm font-semibold">No bets placed yet</p>
              <p className="text-[#4d5063] text-xs mt-1">Pick a match and place a prediction!</p>
            </div>
          ) : (
            predictions.map((p, i) => {
              const match = matches.find((m) => m.match_id === p.match_id);
              const homeFlag = match ? flagUrl(COUNTRY_FLAGS[match.home_team] || "") : "";
              const awayFlag = match ? flagUrl(COUNTRY_FLAGS[match.away_team] || "") : "";
              return (
                <Link key={p.prediction_id} to={`/matches/${p.match_id}`}
                  className="block rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] hover:bg-[#161929] hover:border-[rgba(83,58,253,0.2)] transition-all duration-200 animate-fade-in-up"
                  style={{ animationDelay: `${i * 40}ms` }}>
                  <div className="p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div className="flex items-center gap-4 min-w-0">
                      <span className={`inline-flex items-center rounded-xl px-3 py-1.5 text-xs font-bold uppercase tracking-wider ${
                        p.outcome === "home" ? "bg-[rgba(21,190,83,0.12)] text-[#15be53] border border-[rgba(21,190,83,0.2)]" :
                        p.outcome === "draw" ? "bg-[rgba(229,160,13,0.12)] text-[#e5a00d] border border-[rgba(229,160,13,0.2)]" :
                        "bg-[rgba(59,130,246,0.12)] text-[#3b82f6] border border-[rgba(59,130,246,0.2)]"
                      }`}>{p.outcome}</span>
                      <div className="min-w-0">
                        {match ? (
                          <div className="text-sm font-bold text-[#e8eaf0] flex items-center gap-1.5 truncate">
                            {homeFlag && <img src={homeFlag} alt="" className="w-4 h-3 rounded-sm flex-shrink-0" />}
                            <span className="truncate">{match.home_team}</span>
                            <span className="text-[#4d5063] text-xs font-normal flex-shrink-0">vs</span>
                            <span className="truncate">{match.away_team}</span>
                            {awayFlag && <img src={awayFlag} alt="" className="w-4 h-3 rounded-sm flex-shrink-0" />}
                          </div>
                        ) : (
                          <div className="text-sm font-semibold text-[#7b7f92]">{p.match_id}</div>
                        )}
                        <div className="text-[11px] text-[#4d5063] mt-0.5">
                          {new Date(p.placed_at).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 flex-shrink-0">
                      <span className="text-sm font-bold text-[#e8eaf0] font-mono tabular-nums">{p.stake_usdc} USDC</span>
                      <span className={`text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-xl ${
                        p.settled ? ((p.payout_usdc ?? 0) > 0
                          ? "bg-[rgba(21,190,83,0.12)] text-[#15be53] border border-[rgba(21,190,83,0.2)]"
                          : "bg-[rgba(234,34,97,0.1)] text-[#ea2261] border border-[rgba(234,34,97,0.15)]")
                        : "bg-[rgba(229,160,13,0.1)] text-[#e5a00d] border border-[rgba(229,160,13,0.15)]"
                      }`}>
                        {p.settled ? ((p.payout_usdc ?? 0) > 0 ? `Won +${p.payout_usdc} USDC` : "Lost") : "Pending"}
                      </span>
                    </div>
                  </div>
                </Link>
              );
            })
          )}
        </div>
      )}

      {/* Match grid */}
      {filter !== "mybets" && (
        <>
          {filtered.length === 0 ? (
            <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-10 text-center">
              <p className="text-[#7b7f92] text-sm font-semibold">No {filter} matches</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((m, i) => {
                const homeFlag = flagUrl(COUNTRY_FLAGS[m.home_team] || "");
                const awayFlag = flagUrl(COUNTRY_FLAGS[m.away_team] || "");
                const isLive = m.status === "live";
                const isUpcoming = m.status === "scheduled";
                const isFinished = m.status === "finished";
                const countdownText = getCountdown(m.kickoff_utc);
                return (
                  <Link key={m.match_id} to={`/matches/${m.match_id}`}
                    className={`block rounded-2xl border transition-all duration-200 animate-fade-in-up hover:border-[rgba(83,58,253,0.2)] ${
                      isLive ? "border-[rgba(234,34,97,0.2)] bg-gradient-to-r from-[#11131f] to-[rgba(234,34,97,0.03)] hover:to-[rgba(234,34,97,0.06)]"
                        : "border-[rgba(83,58,253,0.08)] bg-[#11131f] hover:bg-[#161929]"
                    }`}
                    style={{ animationDelay: `${i * 40}ms` }}>
                    <div className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <span className="text-sm sm:text-base font-bold text-[#e8eaf0] truncate flex items-center gap-2">
                          {homeFlag && <img src={homeFlag} alt="" className="w-5 h-3.5 rounded-sm flex-shrink-0" />}
                          <span className="truncate">{m.home_team}</span>
                        </span>
                        <span className="text-[#4d5063] text-xs font-semibold flex-shrink-0">vs</span>
                        <span className="text-sm sm:text-base font-bold text-[#e8eaf0] truncate flex items-center gap-2">
                          <span className="truncate">{m.away_team}</span>
                          {awayFlag && <img src={awayFlag} alt="" className="w-5 h-3.5 rounded-sm flex-shrink-0" />}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 flex-shrink-0">
                        {m.home_score !== null && m.away_score !== null ? (
                          <span className="text-lg font-bold text-[#e8eaf0] tabular-nums font-mono">
                            {m.home_score} <span className="text-[#4d5063] font-normal">—</span> {m.away_score}
                          </span>
                        ) : isUpcoming ? (
                          <span className="text-xs font-bold text-[#a89ffa] tabular-nums animate-pulse px-2.5 py-1 rounded-xl bg-[rgba(83,58,253,0.08)] border border-[rgba(83,58,253,0.15)]">
                            ⏳ {countdownText}
                          </span>
                        ) : null}
                        <span className={`text-[11px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-xl ${
                          isLive ? "bg-[rgba(234,34,97,0.12)] text-[#ea2261] border border-[rgba(234,34,97,0.2)]"
                            : isFinished ? "bg-[rgba(77,80,99,0.15)] text-[#7b7f92] border border-[rgba(77,80,99,0.15)]"
                            : "bg-[rgba(83,58,253,0.1)] text-[#a89ffa] border border-[rgba(83,58,253,0.15)]"
                        }`}>
                          {isLive && <span className="w-1.5 h-1.5 rounded-full bg-[#ea2261] inline-block mr-1.5 animate-[live-dot_1.5s_infinite] align-middle" />}
                          {m.status}
                        </span>
                        <span className="text-xs text-[#4d5063] w-20 text-right tabular-nums hidden sm:inline">
                          {new Date(m.kickoff_utc).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
