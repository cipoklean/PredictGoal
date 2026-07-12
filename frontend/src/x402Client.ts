// x402 payment client for the browser.
//
// Uses the official x402 v2 JS client (@x402/fetch + @x402/evm) with a
// MetaMask (window.ethereum) signer. When a wallet is connected, `getPaymentFetch()`
// returns a fetch wrapper that automatically handles HTTP 402 responses by signing
// an x402 payment proof and retrying — matching the backend's x402 v2 server.
//
// Enforcement is server-side: the backend only requires payment when
// X402_PAYMENT_RECIPIENT is configured. With no recipient set, requests succeed
// (dev passthrough) and no MetaMask popup happens.

import { wrapFetchWithPaymentFromConfig } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm";
import { createWalletClient, custom, defineChain, type WalletClient } from "viem";

// Injective EVM testnet — the chain the x402 fee is paid on (chain ID 888).
// Users add this network to MetaMask so the prediction fee settles "on
// Injective" rather than on a foreign L2.
export const injectiveEvmTestnet = defineChain({
  id: 888,
  name: "Injective EVM Testnet",
  nativeCurrency: { name: "INJ", symbol: "INJ", decimals: 18 },
  rpcUrls: {
    default: { http: ["https://testnet.evm.injective.network"] },
  },
  testnet: true,
});

type AnyFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

let paymentFetch: AnyFetch | null = null;
let paymentAddress = "";

export function isPaymentAvailable(): boolean {
  return typeof window !== "undefined" && !!(window as any).ethereum;
}

export function isPaymentConnected(): boolean {
  return paymentFetch !== null;
}

export function getPaymentAddress(): string {
  return paymentAddress;
}

export function getPaymentFetch(): AnyFetch | null {
  return paymentFetch;
}

export async function connectPaymentWallet(): Promise<string> {
  const eth = (window as any).ethereum;
  if (!eth) {
    throw new Error("No EVM wallet found. Install MetaMask to pay with x402.");
  }
  const accounts = (await eth.request({ method: "eth_requestAccounts" })) as string[];
  const addr = accounts?.[0];
  if (!addr) throw new Error("No account authorized in wallet.");

  // viem wallet client backed by the injected MetaMask provider, pinned to the
  // Injective EVM testnet (chain 888) so MetaMask switches to the right network
  // and the signed fee tx settles on Injective. The x402 client still selects
  // the exact network (eip155:888) from the server's 402 requirements.
  const walletClient = createWalletClient({
    account: addr as `0x${string}`,
    chain: injectiveEvmTestnet,
    transport: custom(eth),
  }) as WalletClient;

  paymentFetch = wrapFetchWithPaymentFromConfig(fetch, {
    schemes: [
      {
        network: "eip155:*",
        client: new ExactEvmScheme(walletClient as any),
      },
    ],
  }) as AnyFetch;

  paymentAddress = addr;
  return addr;
}

export function disconnectPaymentWallet() {
  paymentFetch = null;
  paymentAddress = "";
}
