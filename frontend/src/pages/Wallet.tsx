import { useState } from "react";
import { api } from "../api";

interface Props {
  walletAddress: string;
}

export default function WalletPage({ walletAddress }: Props) {
  const [amount, setAmount] = useState(10);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"success" | "error">("success");
  const [loading, setLoading] = useState(false);

  const doAction = async (action: "deposit" | "withdraw") => {
    setLoading(true); setMsg("");
    try {
      const r = action === "deposit" ? await api.deposit(amount) : await api.withdraw(amount);
      setMsgType("success");
      setMsg(`${action === "deposit" ? "Deposited" : "Withdrew"} ${amount} USDC &middot; tx: ${r.tx_hash.slice(0, 14)}...`);
    } catch (e: unknown) {
      setMsgType("error");
      setMsg(e instanceof Error ? e.message : "Unknown error");
    } finally { setLoading(false); }
  };

  const noAddress = !walletAddress;

  return (
    <div className="max-w-lg mx-auto px-4 sm:px-6 animate-fade-in-up space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-[#e8eaf0] tracking-tight">Wallet</h1>
        <p className="text-sm text-[#7b7f92] mt-1">Manage your testnet USDC for predictions</p>
      </div>

      {/* Active address */}
      <div className="rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-5">
        <div className="text-xs font-bold text-[#7b7f92] uppercase tracking-widest mb-2">Active Address</div>
        <div className="flex items-center gap-2.5">
          <span className={`w-2.5 h-2.5 rounded-full shadow-[0_0_8px_rgba(21,190,83,0.5)] ${
            noAddress ? "bg-[#4d5063]" : "bg-[#15be53] animate-[breathe_2s_infinite]"
          }`} />
          <span className="text-sm font-semibold text-[#e8eaf0] font-mono">
            {walletAddress || "No address set — use the Set Address button in the navbar"}
          </span>
        </div>
      </div>

      {/* Transfer — disabled if no address */}
      <div className={`rounded-2xl border border-[rgba(83,58,253,0.1)] bg-[#11131f] p-5 sm:p-6 ${noAddress ? "opacity-50" : ""}`}>
        <h2 className="text-xs font-bold text-[#7b7f92] uppercase tracking-widest mb-5">CCTP Transfer</h2>

        <div className="mb-4">
          <label className="block text-xs font-bold text-[#7b7f92] uppercase tracking-widest mb-2">Amount (USDC)</label>
          <div className="relative">
            <input
              type="number" min={0.1} step={1}
              value={amount} onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
              disabled={noAddress}
              className="w-full rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(83,58,253,0.12)] px-4 py-3 text-sm font-semibold text-[#e8eaf0] outline-none focus:border-[#533afd] focus:ring-2 focus:ring-[#533afd]/20 transition-all duration-200 disabled:opacity-40"
            />
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-[#4d5063]">USDC</span>
          </div>
        </div>

        <div className="flex gap-2">
          <button onClick={() => doAction("deposit")} disabled={loading || amount <= 0 || noAddress}
            className="flex-1 py-3 rounded-xl text-sm font-bold transition-all duration-200 active:scale-[0.97]
              bg-gradient-to-br from-[#15be53] to-[#0dd85f] hover:from-[#16c958] hover:to-[#0ee865] disabled:from-[#1e2140] disabled:to-[#1e2140] disabled:text-[#4d5063] text-white shadow-[0_0_16px_rgba(21,190,83,0.2)]">
            Deposit
          </button>
          <button onClick={() => doAction("withdraw")} disabled={loading || amount <= 0 || noAddress}
            className="flex-1 py-3 rounded-xl text-sm font-bold transition-all duration-200 active:scale-[0.97]
              bg-[rgba(255,255,255,0.04)] border border-[rgba(83,58,253,0.15)] text-[#e8eaf0] hover:bg-[rgba(255,255,255,0.08)] disabled:opacity-40 disabled:cursor-not-allowed">
            Withdraw
          </button>
        </div>

        {msg && (
          <div className={`mt-4 text-xs font-semibold rounded-xl px-4 py-2.5 animate-fade-in-up ${
            msgType === "error" ? "bg-[rgba(234,34,97,0.1)] text-[#ea2261] border border-[rgba(234,34,97,0.2)]"
              : "bg-[rgba(21,190,83,0.1)] text-[#15be53] border border-[rgba(21,190,83,0.2)]"
          }`} dangerouslySetInnerHTML={{ __html: msg }} />
        )}
      </div>

      {/* Faucet */}
      <div className="rounded-2xl bg-[rgba(83,58,253,0.04)] border border-[rgba(83,58,253,0.1)] p-5">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-[#a89ffa] mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0Z" />
          </svg>
          <div>
            <p className="text-sm font-bold text-[#e8eaf0]">Testnet Faucet</p>
            <p className="text-xs text-[#7b7f92] mt-1 leading-relaxed">
              Claim free INJ from{" "}
              <a href="https://testnet.faucet.injective.network" target="_blank"
                className="text-[#a89ffa] hover:text-[#c4bbff] font-semibold transition underline underline-offset-2">
                testnet.faucet.injective.network
              </a>
            </p>
            <p className="text-[11px] text-[#4d5063] mt-2">Predictions cost 2.0 USDC each (x402 fee) &middot; Max 100 USDC stake &middot; Zero real funds</p>
          </div>
        </div>
      </div>
    </div>
  );
}
