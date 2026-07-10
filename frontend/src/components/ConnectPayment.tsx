import { useState } from "react";
import { connectPaymentWallet, disconnectPaymentWallet, isPaymentAvailable } from "../x402Client";

interface Props {
  onAddress: (addr: string) => void;
}

// MetaMask connect button that enables x402 payment signing for predictions/insights.
// When connected, the unified wallet address (used for X-User-Address) is set to the
// MetaMask account so identity and payer match.
export default function ConnectPayment({ onAddress }: Props) {
  const [connected, setConnected] = useState(false);
  const [addr, setAddr] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Hide entirely if the browser has no injected EVM wallet.
  if (!isPaymentAvailable()) return null;

  const handleConnect = async () => {
    setBusy(true);
    setError("");
    try {
      const a = await connectPaymentWallet();
      setAddr(a);
      setConnected(true);
      onAddress(a);
    } catch (e: any) {
      setError(e?.message || "Failed to connect wallet");
    } finally {
      setBusy(false);
    }
  };

  const handleDisconnect = () => {
    disconnectPaymentWallet();
    setConnected(false);
    setAddr("");
  };

  if (connected) {
    return (
      <div className="flex items-center gap-1.5 rounded-xl bg-[rgba(245,166,35,0.08)] border border-[rgba(245,166,35,0.18)] px-2.5 py-1.5 animate-scale-in">
        <span className="text-[#f5a623] text-xs font-bold">⚡ x402</span>
        <span className="font-mono text-xs text-[#e8eaf0]">{addr.slice(0, 6)}…{addr.slice(-4)}</span>
        <button
          onClick={handleDisconnect}
          className="text-[#4d5063] hover:text-[#e8eaf0] text-xs px-1 transition"
          title="Disconnect payments"
        >
          ✕
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={handleConnect}
      disabled={busy}
      className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[#f5a623] to-[#f7c948] text-black text-xs font-bold px-3 py-2 hover:from-[#e09412] hover:to-[#e6b73a] active:scale-[0.97] transition shadow-[0_0_12px_rgba(245,166,35,0.25)] disabled:opacity-60"
      title={error || "Connect MetaMask to pay predictions with x402"}
    >
      {busy ? "Connecting…" : "⚡ Connect Payments"}
    </button>
  );
}
