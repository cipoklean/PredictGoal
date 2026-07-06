import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
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
    <nav className="bg-gray-900 border-b border-gray-800 sticky top-0 z-10">
      <div className="max-w-4xl mx-auto px-4 flex items-center justify-between h-14">
        <Link to="/" className="text-white font-bold text-lg tracking-tight">
          ⚽ PredictGoal
        </Link>
        <div className="flex gap-1">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                location.pathname === link.to
                  ? "bg-indigo-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-300">
        <Navbar />
        <main className="py-6">
          <Routes>
            <Route path="/" element={<MatchesPage />} />
            <Route path="/matches/:id" element={<MatchDetailPage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route path="/wallet" element={<WalletPage />} />
          </Routes>
        </main>
        <footer className="text-center text-gray-600 text-xs py-6 border-t border-gray-800">
          PredictGoal — Testnet Only — No Real Funds
        </footer>
      </div>
    </BrowserRouter>
  );
}
