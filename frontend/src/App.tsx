import { useState, useCallback, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import ConnectWallet from "./components/ConnectWallet";
import ConnectPayment from "./components/ConnectPayment";
import { setWalletAddress as updateApiWallet } from "./api";
import { disconnectPaymentWallet } from "./x402Client";
import MatchesPage from "./pages/Matches";
import MatchDetailPage from "./pages/MatchDetail";
import LeaderboardPage from "./pages/Leaderboard";
import WalletPage from "./pages/Wallet";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

function Navbar({
  walletAddress,
  onConnect,
  onDisconnect,
  balance,
}: {
  walletAddress: string;
  onConnect: (addr: string) => void;
  onDisconnect: () => void;
  balance: number | null;
}) {
  const location = useLocation();
  const links = [
    { to: "/", label: "Matches" },
    { to: "/leaderboard", label: "Leaderboard" },
    { to: "/wallet", label: "Wallet" },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-[rgba(83,58,253,0.1)]"
      style={{ background: "rgba(10,11,20,0.85)", backdropFilter: "blur(24px)" }}>
      <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-16">
        <Link to="/" className="flex items-center gap-3 text-[#e8eaf0] font-semibold text-base tracking-tight hover:opacity-90 transition">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#533afd] to-[#7b6ff0] flex items-center justify-center text-white text-sm font-bold shadow-[0_0_16px_rgba(83,58,253,0.3)]">
            P
          </div>
          <span className="hidden sm:inline">PredictGoal</span>
        </Link>

        <div className="flex items-center gap-1">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                location.pathname === link.to
                  ? "bg-[rgba(83,58,253,0.12)] text-[#a89ffa]"
                  : "text-[#7b7f92] hover:text-[#e8eaf0] hover:bg-[rgba(255,255,255,0.03)]"
              }`}
            >
              {link.label}
            </Link>
          ))}

          {walletAddress && balance !== null && (
            <span className="text-xs font-semibold text-[#15be53] bg-[rgba(21,190,83,0.1)] border border-[rgba(21,190,83,0.2)] rounded-lg px-2.5 py-1 font-mono tabular-nums mr-2 animate-count-up">
              {balance.toFixed(1)} USDC
            </span>
          )}

          <ConnectWallet address={walletAddress} onConnect={onConnect} onDisconnect={onDisconnect} />
          <ConnectPayment showConnectButton={false} />
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  const [walletAddress, setWalletAddress] = useState("");
  const [balance, setBalance] = useState<number | null>(null);

  const fetchBalance = useCallback(async (addr: string) => {
    try {
      const res = await fetch(`${API_BASE}/wallet/balance`, {
        headers: { "X-User-Address": addr },
      });
      if (res.ok) {
        const data = await res.json();
        setBalance(data.balance_usdc);
      }
    } catch {
      setBalance(null);
    }
  }, []);

  const handleConnect = (addr: string) => {
    setWalletAddress(addr);
    updateApiWallet(addr);
    fetchBalance(addr);
  };

  const handleDisconnect = () => {
    disconnectPaymentWallet();
    setWalletAddress("");
    setBalance(null);
  };

  // Poll balance every 10s while wallet is connected
  useEffect(() => {
    if (!walletAddress) return;
    const interval = setInterval(() => fetchBalance(walletAddress), 10000);
    return () => clearInterval(interval);
  }, [walletAddress, fetchBalance]);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0a0b14] text-[#e8eaf0]">
        <Navbar walletAddress={walletAddress} onConnect={handleConnect} onDisconnect={handleDisconnect} balance={balance} />
        <main className="py-10">
          <Routes>
            <Route path="/" element={<MatchesPage />} />
            <Route path="/matches/:id" element={<MatchDetailPage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route path="/wallet" element={<WalletPage walletAddress={walletAddress} />} />
          </Routes>
        </main>
        <footer className="text-center text-[#4d5063] text-xs py-8 border-t border-[rgba(83,58,253,0.08)]">
          PredictGoal &middot; Injective Global Cup Hackathon &middot; Testnet Only &middot; No Real Funds
        </footer>
      </div>
    </BrowserRouter>
  );
}
