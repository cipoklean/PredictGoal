import { getPaymentFetch, getPaymentAddress, isPaymentConnected } from "./x402Client";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

// Canonical account identity is the user's "Set Address" (navbar identity),
// persisted so it survives page refresh and wallet (dis)connect.
// The MetaMask / x402 wallet is ONLY a payment signer — it must NEVER be used
// as the account key, otherwise bets & balance flip to a different backend user
// the moment the payment wallet is disconnected.
const LS_KEY = "predictgoal_address";

function _loadSavedAddress(): string {
  try {
    if (typeof localStorage !== "undefined") {
      return localStorage.getItem(LS_KEY) || "";
    }
  } catch {
    /* localStorage unavailable — fall through */
  }
  return "";
}

let _walletAddress = _loadSavedAddress();

export function setWalletAddress(addr: string) {
  _walletAddress = addr;
  try {
    if (typeof localStorage !== "undefined") {
      if (addr) localStorage.setItem(LS_KEY, addr);
      else localStorage.removeItem(LS_KEY);
    }
  } catch {
    /* ignore persistence errors */
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const send = getPaymentFetch() ?? fetch;
  // Identity = the "Set Address" the user chose as their account. The MetaMask
  // (x402) wallet is ONLY a payment signer and must NOT be the account key —
  // otherwise bets/balance flip to a different backend user the moment the
  // payment wallet is disconnected. Fall back to the payment address only when
  // no Set Address has been chosen yet (keeps MetaMask-only betting working in
  // the current session).
  const userAddr = _walletAddress || (isPaymentConnected() ? getPaymentAddress() : "");
  const res = await send(`${API_BASE}${url}`, {
    headers: {
      "Content-Type": "application/json",
      "X-User-Address": userAddr || "",
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

  getPremiumInsight: (id: string) =>
    request<{
      match_id: string;
      home_team: string;
      away_team: string;
      win_prob_home: number;
      win_prob_draw: number;
      win_prob_away: number;
      momentum: Record<string, unknown>;
      form_analysis: Record<string, unknown>;
      key_player_impact: Record<string, unknown>;
      data_source: string;
      disclaimer: string;
    }>(`/insights/${id}`),

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
