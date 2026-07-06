import { useState } from "react";

interface Props {
  address: string;
  onConnect: (addr: string) => void;
  onDisconnect: () => void;
}

export default function ConnectWallet({ address, onConnect, onDisconnect }: Props) {
  const [inputValue, setInputValue] = useState("");
  const [showInput, setShowInput] = useState(false);

  const handleClick = () => {
    if (address) { onDisconnect(); return; }
    setShowInput(true);
  };

  const submitAddress = (e: React.FormEvent) => {
    e.preventDefault();
    const addr = inputValue.trim();
    if (addr.length >= 8) { onConnect(addr); setShowInput(false); setInputValue(""); }
  };

  if (showInput) return (
    <form onSubmit={submitAddress} className="flex items-center gap-1.5 animate-scale-in">
      <input type="text" placeholder="inj1... or 0x..." value={inputValue}
        onChange={(e) => setInputValue(e.target.value)} autoFocus
        className="w-40 rounded-xl bg-[rgba(255,255,255,0.04)] border border-[rgba(83,58,253,0.2)] px-3 py-2 text-xs font-semibold text-[#e8eaf0] font-mono outline-none focus:border-[#533afd] focus:ring-2 focus:ring-[#533afd]/20 transition" />
      <button type="submit" className="bg-gradient-to-br from-[#533afd] to-[#7b6ff0] text-white text-xs font-bold px-3 py-2 rounded-xl hover:from-[#4434d4] transition shadow-[0_0_12px_rgba(83,58,253,0.3)]">Set</button>
      <button type="button" onClick={() => setShowInput(false)} className="text-[#4d5063] hover:text-[#7b7f92] text-xs px-1.5 py-1.5 transition">✕</button>
    </form>
  );

  return (
    <button onClick={handleClick}
      className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold transition-all duration-200 ${
        address
          ? "bg-[rgba(83,58,253,0.08)] border border-[rgba(83,58,253,0.15)] text-[#a89ffa] hover:bg-[rgba(83,58,253,0.14)]"
          : "bg-gradient-to-br from-[#533afd] to-[#7b6ff0] text-white hover:from-[#4434d4] hover:to-[#6b5fe0] active:scale-[0.97] shadow-[0_0_16px_rgba(83,58,253,0.25)]"
      }`}>
      {address && (
        <span className="relative flex h-2 w-2 flex-shrink-0">
          <span className="absolute inline-flex h-full w-full rounded-full bg-[#15be53] animate-[breathe_2s_infinite]" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-[#15be53]" />
        </span>
      )}
      <span className="font-mono text-xs truncate max-w-[120px]">{address || "Connect Wallet"}</span>
      {address && (
        <span className="bg-[rgba(83,58,253,0.2)] text-[#c4bbff] text-[9px] font-bold uppercase px-2 py-0.5 rounded-lg">Demo</span>
      )}
    </button>
  );
}
