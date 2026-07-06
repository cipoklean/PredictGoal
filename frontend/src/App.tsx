import { useState, useCallback } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import ConnectWallet from "./components/ConnectWallet";
import { setWalletAddress as updateApiWallet } from "./api";
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
    <nav
      className="sticky top-0 z-50 border-b border-[#1e1e22]"
      style={{ background: "rgba(8,9,10,0.82)", backdropFilter: "blur(20px)" }}
    >
      <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-14">
        <Link
          to="/"
          className="flex items-center gap-2.5 text-[#f7f8f8] font-semibold text-[15px] tracking-tight hover:opacity-90 transition"
        >
          <span className="w-7 h-7 rounded-lg bg-[#5e6ad2] flex items-center justify-center text-white text-xs font-bold">
            P
          </span>
          PredictGoal
        </Link>
        <div className="flex items-center gap-1">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-all duration-150 ${
                location.pathname === link.to
                  ? "bg-[#16181a] text-[#f7f8f8]"
                  : "text-[#8a8f98] hover:text-[#d0d6e0] hover:bg-[rgba(255,255,255,0.03)]"
              }`}
            >
              {link.label}
            </Link>
          ))}
          {walletAddress && balance !== null && (
            <span className="text-[12px] font-medium text-[#27a644] mr-1 font-mono tabular-nums">
              {balance.toFixed(1)} USDC
            </span>
          )}
          <div className="ml-3">
            <ConnectWallet
              address={walletAddress}
              onConnect={onConnect}
              onDisconnect={onDisconnect}
            />
          </div>
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
    updateApiWallet(addr); // so all API calls send the connected address
    fetchBalance(addr);
  };

  const handleDisconnect = () => {
    setWalletAddress("");
    setBalance(null);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#08090a] text-[#d0d6e0]">
        <Navbar
          walletAddress={walletAddress}
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
          balance={balance}
        />
        <main className="py-8">
          <Routes>
            <Route path="/" element={<MatchesPage />} />
            <Route path="/matches/:id" element={<MatchDetailPage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route path="/wallet" element={<WalletPage />} />
          </Routes>
        </main>
        <footer className="text-center text-[#62666d] text-[11px] py-6 border-t border-[#1e1e22]">
          PredictGoal &middot; Injective Global Cup Hackathon &middot; Testnet Only &middot; No Real Funds
        </footer>
      </div>
    </BrowserRouter>
  );
}
