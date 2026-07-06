import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Match } from "../api";

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

type Filter = "all" | "live" | "upcoming" | "finished";

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getMatches()
      .then((res) => setMatches(res.matches))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = matches.filter((m) => {
    if (filter === "all") return true;
    if (filter === "live") return m.status === "live";
    if (filter === "upcoming") return m.status === "scheduled";
    if (filter === "finished") return m.status === "finished";
    return true;
  });

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 animate-fade-in-up">
        <div className="h-8 w-48 skeleton rounded mb-6" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-20 skeleton rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-6 animate-fade-in-up">
        <div className="rounded-xl border border-[#23252a] bg-[#16181a] p-8 text-center">
          <p className="text-[#ef4444] text-sm font-medium">Failed to load matches</p>
          <p className="text-[#62666d] text-xs mt-1">{error}</p>
        </div>
      </div>
    );
  }

  const counts = {
    all: matches.length,
    live: matches.filter((m) => m.status === "live").length,
    upcoming: matches.filter((m) => m.status === "scheduled").length,
    finished: matches.filter((m) => m.status === "finished").length,
  };

  return (
    <div className="max-w-4xl mx-auto px-6 animate-fade-in-up">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-[22px] font-semibold text-[#f7f8f8] tracking-tight">Matches</h1>
        <span className="text-[13px] text-[#62666d] font-medium">{counts.live} live &middot; {counts.upcoming} upcoming</span>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-6">
        {(["all", "live", "upcoming", "finished"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-all duration-150 capitalize ${
              filter === f
                ? "bg-[#16181a] text-[#f7f8f8]"
                : "text-[#8a8f98] hover:text-[#d0d6e0]"
            }`}
          >
            {f}
            <span className="ml-1.5 text-[#62666d]">{counts[f]}</span>
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-xl border border-[#23252a] bg-[#16181a] p-8 text-center">
          <p className="text-[#8a8f98] text-sm">No {filter} matches</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((m, i) => {
            const homeFlag = flagUrl(COUNTRY_FLAGS[m.home_team] || "");
            const awayFlag = flagUrl(COUNTRY_FLAGS[m.away_team] || "");

            return (
              <Link
                key={m.match_id}
                to={`/matches/${m.match_id}`}
                className="block rounded-xl border border-[#23252a] bg-[#0f1011] hover:bg-[#141518] hover:border-[#34343a] transition-all duration-200 animate-fade-in-up"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-[15px] font-medium text-[#f7f8f8] truncate flex items-center gap-1.5">
                        {homeFlag && <img src={homeFlag} alt="" className="w-5 h-3.5 rounded-sm opacity-80" />}
                        {m.home_team}
                      </span>
                      <span className="text-[#62666d] text-[13px] font-medium">vs</span>
                      <span className="text-[15px] font-medium text-[#f7f8f8] truncate flex items-center gap-1.5">
                        {m.away_team}
                        {awayFlag && <img src={awayFlag} alt="" className="w-5 h-3.5 rounded-sm opacity-80" />}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 flex-shrink-0">
                    {m.home_score !== null && m.away_score !== null && (
                      <span className="text-lg font-semibold text-[#f7f8f8] tabular-nums">
                        {m.home_score} <span className="text-[#8a8f98]">—</span> {m.away_score}
                      </span>
                    )}
                    <span className={`text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded ${
                      m.status === "live"
                        ? "bg-[#ef4444]/10 text-[#ef4444]"
                        : m.status === "finished"
                        ? "bg-[#62666d]/10 text-[#62666d]"
                        : "bg-[#5e6ad2]/10 text-[#7170ff]"
                    }`}>
                      {m.status === "live" && <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#ef4444] mr-1.5 animate-live align-middle" />}
                      {m.status}
                    </span>
                    <span className="text-[12px] text-[#62666d] w-20 text-right tabular-nums">
                      {new Date(m.kickoff_utc).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
