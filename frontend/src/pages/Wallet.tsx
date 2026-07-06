import { useState } from "react";
import { api } from "../api";

export default function WalletPage() {
  const [amount, setAmount] = useState(10);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const doDeposit = async () => {
    setLoading(true);
    setMsg("");
    try {
      const r = await api.deposit(amount);
      setMsg(`Deposited ${r.success ? "successfully" : "failed"}: ${r.tx_hash.slice(0, 20)}...`);
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const doWithdraw = async () => {
    setLoading(true);
    setMsg("");
    try {
      const r = await api.withdraw(amount);
      setMsg(`Withdrew ${r.success ? "successfully" : "failed"}: ${r.tx_hash.slice(0, 20)}...`);
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-3xl font-bold text-white mb-6">Wallet</h1>
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-4">
        <div className="text-gray-400 text-sm mb-1">Connected Address</div>
        <div className="text-white font-mono text-sm">
          inj1testuser0000000000000000000000
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h2 className="text-lg font-semibold text-white mb-3">CCTP Transfer</h2>
        <div className="mb-3">
          <label className="text-gray-400 text-sm block mb-1">Amount (USDC)</label>
          <input
            type="number"
            min={0.1}
            step={1}
            value={amount}
            onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
            className="w-full bg-gray-700 rounded px-3 py-2 text-white border border-gray-600"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={doDeposit}
            disabled={loading || amount <= 0}
            className="flex-1 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 text-white py-2 rounded font-semibold"
          >
            Deposit
          </button>
          <button
            onClick={doWithdraw}
            disabled={loading || amount <= 0}
            className="flex-1 bg-red-600 hover:bg-red-500 disabled:bg-gray-600 text-white py-2 rounded font-semibold"
          >
            Withdraw
          </button>
        </div>
        {msg && (
          <div className={`mt-3 text-sm ${msg.startsWith("Error") ? "text-red-400" : "text-green-400"}`}>
            {msg}
          </div>
        )}
      </div>

      <div className="mt-4 bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
        <p className="text-xs text-gray-500">
          Testnet USDC only. Use the Injective testnet faucet at{" "}
          <a href="https://testnet.faucet.injective.network" className="text-indigo-400" target="_blank">
            testnet.faucet.injective.network
          </a>
        </p>
      </div>
    </div>
  );
}
