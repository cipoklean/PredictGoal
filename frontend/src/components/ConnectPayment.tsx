import { useState } from "react";
import { connectPaymentWallet, disconnectPaymentWallet, isPaymentAvailable } from "../x402Client";

interface Props {
  // Navbar usage: when false, render nothing unless already connected (status chip only).
  showConnectButton?: boolean;
  // Custom label for the connect button.
  label?: string;
  // Helper text shown under the button — explains it never auto-charges.
  hint?: string;
  // Called after connect/disconnect so the parent can re-render (does NOT change identity).
  onConnected?: () => void;
  // Called with the connected address — this IS the user's single account
  // (identity = payer). The parent should store it as the active address.
  onAccountSet?: (addr: string) => void;
}

// MetaMask connect button that enables x402 payment signing for predictions/insights.
//
// IMPORTANT: this is SEPARATE from the app identity ("Set Address"). Connecting here
// does NOT change who you are in the app, and connecting never charges anything — a
// payment only happens when you actually click Predict / Unlock and approve the
// MetaMask prompt.
export default function ConnectPayment({
  showConnectButton = true,
  label,
  hint,
  onConnected,
}: Props) {
  const [connected, setConnected] = useState(false);
  const [addr, setAddr] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Hide entirely if the browser has no injected EVM wallet.
  if (!isPaymentAvailable()) return null;
  // Navbar status mode: only show the chip when connected.
  if (!showConnectButton && !connected) return null;

  const handleConnect = async () => {
    setBusy(true);
    setError("");
    try {
      const a = await connectPaymentWallet();
      setAddr(a);
      setConnected(true);
      onAccountSet?.(a);
      onConnected?.();
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
    onConnected?.();
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
    <div className="text-center">
      <button
        onClick={handleConnect}
        disabled={busy}
        className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[#f5a623] to-[#f7c948] text-black text-xs font-bold px-3 py-2 hover:from-[#e09412] hover:to-[#e6b73a] active:scale-[0.97] transition shadow-[0_0_12px_rgba(245,166,35,0.25)] disabled:opacity-60 mx-auto"
        title={error || "Connect MetaMask to pay predictions/insights with x402"}
      >
        {busy ? "Connecting…" : (label || "Connect Wallet")}
      </button>
      {hint && <p className="mt-2 text-[11px] text-[#7b7f92] max-w-xs mx-auto leading-relaxed">{hint}</p>}
      {error && <p className="mt-2 text-[11px] text-[#ea2261] font-semibold">{error}</p>}
    </div>
  );
}
