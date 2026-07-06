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
    if (address) {
      onDisconnect();
      return;
    }
    setShowInput(true);
  };

  const submitAddress = (e: React.FormEvent) => {
    e.preventDefault();
    const addr = inputValue.trim();
    if (addr.length >= 8) {
      onConnect(addr);
      setShowInput(false);
      setInputValue("");
    }
  };

  if (showInput) {
    return (
      <form onSubmit={submitAddress} className="flex items-center gap-1.5 animate-scale-in">
        <input
          type="text"
          placeholder="inj1... or 0x..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className="w-40 rounded-lg bg-[rgba(255,255,255,0.03)] border border-[#23252a] px-3 py-1.5 text-[#f7f8f8] text-xs font-mono outline-none focus:border-[#5e6ad2] focus:ring-1 focus:ring-[#5e6ad2]/20 transition"
          autoFocus
        />
        <button
          type="submit"
          className="bg-[#5e6ad2] text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-[#7170ff] transition"
        >
          Set
        </button>
        <button
          type="button"
          onClick={() => setShowInput(false)}
          className="text-[#62666d] hover:text-[#8a8f98] text-xs px-1.5 py-1.5 transition"
        >
          ✕
        </button>
      </form>
    );
  }

  return (
    <button
      onClick={handleClick}
      className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
        address
          ? "bg-[#16181a] border border-[#23252a] text-[#d0d6e0] hover:border-[#34343a]"
          : "bg-[#5e6ad2] text-white hover:bg-[#7170ff] active:scale-[0.97]"
      }`}
    >
      {address && (
        <span className="relative flex h-2 w-2 flex-shrink-0">
          <span className="absolute inline-flex h-full w-full rounded-full bg-[#27a644] animate-breathe" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-[#27a644]" />
        </span>
      )}
      <span className="font-mono text-xs truncate max-w-[120px]">
        {address || "Connect Wallet"}
      </span>
      {address && (
        <span className="bg-[#5e6ad2]/20 text-[#7170ff] text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded">
          Demo
        </span>
      )}
    </button>
  );
}
