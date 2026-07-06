import { useState } from "react";

export default function ConnectWallet() {
  const [connected, setConnected] = useState(false);
  const [address, setAddress] = useState("Connect Wallet");

  const toggle = () => {
    if (connected) {
      setConnected(false);
      setAddress("Connect Wallet");
    } else {
      setConnected(true);
      setAddress("inj1testuser...");
    }
  };

  return (
    <button
      onClick={toggle}
      className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
        connected
          ? "bg-[#16181a] border border-[#23252a] text-[#d0d6e0] hover:border-[#34343a]"
          : "bg-[#5e6ad2] text-white hover:bg-[#7170ff] active:scale-[0.97]"
      }`}
    >
      {connected && (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full rounded-full bg-[#27a644] animate-breathe" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-[#27a644]" />
        </span>
      )}
      {address}
    </button>
  );
}
