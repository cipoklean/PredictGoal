const API_BASE = import.meta.env.VITE_API_BASE || "/api";

let _walletAddress = "";

export function setWalletAddress(addr: string) {
  _walletAddress = addr;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      "Content-Type": "application/json",
      "X-User-Address": _walletAddress || "",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export interface Match {
  match_id: string;
  home_team: string;
  away_team: string;
  kickoff_utc: string;
  status: string;
  home_score: number | null;
  away_score: number | null;
  odds_home: number | null;
  odds_draw: number | null;
  odds_away: number | null;
}

export interface Prediction {
  prediction_id: string;
  user_address: string;
  match_id: string;
  outcome: string;
  stake_usdc: number;
  placed_at: string;
  tx_hash: string | null;
  settled: boolean;
  payout_usdc: number | null;
}

export interface LeaderboardEntry {
  rank: number;
  user_address: string;
  total_wagered: number;
  total_won: number;
  win_rate: number;
  predictions_count: number;
}

export const api = {
  getMatches: () => request<{ matches: Match[] }>("/matches"),
  getMatch: (id: string) => request<Match>(`/matches/${id}`),
  getMatchAnalytics: (id: string) =>
    request<{
      match_id: string;
      win_prob_home: number;
      win_prob_draw: number;
      win_prob_away: number;
      key_stats: Record<string, unknown>;
    }>(`/matches/${id}/analytics`),

  placePrediction: (data: {
    match_id: string;
    outcome: string;
    stake_usdc: number;
  }) =>
    request<Prediction>("/predictions", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMyPredictions: () => request<Prediction[]>("/predictions/me"),
  getLeaderboard: () => request<LeaderboardEntry[]>("/predictions/leaderboard"),

  deposit: (amount_usdc: number) =>
    request<{ success: boolean; tx_hash: string }>("/wallet/deposit", {
      method: "POST",
      body: JSON.stringify({ amount_usdc }),
    }),

  withdraw: (amount_usdc: number) =>
    request<{ success: boolean; tx_hash: string }>("/wallet/withdraw", {
      method: "POST",
      body: JSON.stringify({ amount_usdc }),
    }),

  getBalance: () =>
    request<{ user_address: string; balance_usdc: number }>("/wallet/balance"),
};
