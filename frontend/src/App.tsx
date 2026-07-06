import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import ConnectWallet from "./components/ConnectWallet";
import MatchesPage from "./pages/Matches";
import MatchDetailPage from "./pages/MatchDetail";
import LeaderboardPage from "./pages/Leaderboard";
import WalletPage from "./pages/Wallet";

function Navbar() {
  const location = useLocation();

  const links = [
    { to: "/", label: "Matches" },
    { to: "/leaderboard", label: "Leaderboard" },
    { to: "/wallet", label: "Wallet" },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-[#1e1e22]"
      style={{ background: "rgba(8,9,10,0.82)", backdropFilter: "blur(20px)" }}>
      <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-14">
        <Link to="/" className="flex items-center gap-2.5 text-[#f7f8f8] font-semibold text-[15px] tracking-tight hover:opacity-90 transition">
          <span className="w-7 h-7 rounded-lg bg-[#5e6ad2] flex items-center justify-center text-white text-xs font-bold">P</span>
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
          <div className="ml-3">
            <ConnectWallet />
          </div>
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#08090a] text-[#d0d6e0]">
        <Navbar />
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
