import { useState } from "react";
import { api } from "../api";

export default function WalletPage() {
  const [amount, setAmount] = useState(10);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"success" | "error">("success");
  const [loading, setLoading] = useState(false);

  const doAction = async (action: "deposit" | "withdraw") => {
    setLoading(true);
    setMsg("");
    try {
      const r = action === "deposit" ? await api.deposit(amount) : await api.withdraw(amount);
      setMsgType("success");
      setMsg(`${action === "deposit" ? "Deposited" : "Withdrew"} ${amount} USDC successfully · tx: ${r.tx_hash.slice(0, 16)}...`);
    } catch (e: unknown) {
      setMsgType("error");
      setMsg(`Error: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto px-6 animate-fade-in-up space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold text-[#f7f8f8] tracking-tight">Wallet</h1>
        <p className="text-[13px] text-[#62666d] mt-1">Manage your testnet USDC for predictions</p>
      </div>

      {/* Connected address card */}
      <div className="rounded-xl border border-[#23252a] bg-[#0f1011] p-4">
        <div className="text-[11px] font-semibold text-[#8a8f98] uppercase tracking-wider mb-1">Connected Address</div>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-[#27a644] animate-breathe" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-[#27a644]" />
          </span>
          <span className="text-[#d0d6e0] text-sm font-medium font-mono">inj1testuser...0000</span>
        </div>
      </div>

      {/* Transfer card */}
      <div className="rounded-xl border border-[#23252a] bg-[#0f1011] p-5">
        <h2 className="text-[13px] font-semibold text-[#8a8f98] uppercase tracking-wider mb-4">CCTP Transfer</h2>

        {/* Amount input */}
        <div className="mb-4">
          <label className="block text-[11px] font-semibold text-[#8a8f98] uppercase tracking-wider mb-1.5">Amount (USDC)</label>
          <div className="relative">
            <input
              type="number"
              min={0.1}
              step={1}
              value={amount}
              onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
              className="w-full rounded-lg bg-[rgba(255,255,255,0.03)] border border-[#23252a] px-4 py-2.5 text-[#f7f8f8] text-sm font-medium outline-none focus:border-[#5e6ad2] focus:ring-1 focus:ring-[#5e6ad2]/20 transition-all duration-200"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[#62666d] text-xs font-medium">USDC</span>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => doAction("deposit")}
            disabled={loading || amount <= 0}
            className="flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 active:scale-[0.97]
              bg-[#27a644] hover:bg-[#2db84d] disabled:bg-[#23252a] disabled:text-[#62666d] text-white"
          >
            Deposit
          </button>
          <button
            onClick={() => doAction("withdraw")}
            disabled={loading || amount <= 0}
            className="flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 active:scale-[0.97]
              bg-[rgba(255,255,255,0.04)] border border-[#23252a] text-[#d0d6e0] hover:bg-[rgba(255,255,255,0.08)] disabled:opacity-40"
          >
            Withdraw
          </button>
        </div>

        {/* Message */}
        {msg && (
          <div className={`mt-3 text-[12px] font-medium rounded-lg px-3 py-2 animate-fade-in-up ${
            msgType === "error"
              ? "bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/20"
              : "bg-[#27a644]/10 text-[#27a644] border border-[#27a644]/20"
          }`}>
            {msg}
          </div>
        )}
      </div>

      {/* Faucet info */}
      <div className="rounded-xl bg-[rgba(94,106,210,0.04)] border border-[#5e6ad2]/10 p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-[#7170ff] mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
          <div>
            <p className="text-[13px] font-semibold text-[#f7f8f8]">Testnet Faucet</p>
            <p className="text-[12px] text-[#8a8f98] mt-0.5 leading-relaxed">
              Need testnet USDC? This runs on Injective testnet — claim free INJ from{" "}
              <a href="https://testnet.faucet.injective.network" target="_blank" className="text-[#7170ff] hover:text-[#828fff] font-medium transition">
                testnet.faucet.injective.network
              </a>
            </p>
            <p className="text-[11px] text-[#62666d] mt-2">
              Predictions cost 0.1 USDC each · Max stake 100 USDC · Zero real funds
            </p>
          </div>
        </div>
      </div>

      {/* Injective ecosystem links */}
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: "Injective Explorer", href: "https://testnet.explorer.injective.network" },
          { label: "Injective Docs", href: "https://docs.injective.network" },
          { label: "Circle CCTP", href: "https://www.circle.com/en/cross-chain-transfer-protocol" },
          { label: "x402 Protocol", href: "https://docs.injective.network" },
        ].map(({ label, href }) => (
          <a
            key={label}
            href={href}
            target="_blank"
            className="rounded-lg border border-[#23252a] bg-[rgba(255,255,255,0.02)] px-4 py-2.5 text-[12px] text-[#8a8f98] hover:text-[#d0d6e0] hover:border-[#34343a] transition-all duration-200 text-center"
          >
            {label} ↗
          </a>
        ))}
      </div>
    </div>
  );
}
