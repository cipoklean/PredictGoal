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
import { createWalletClient, custom, type WalletClient } from "viem";
import { baseSepolia } from "viem/chains";

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

  // viem wallet client backed by the injected MetaMask provider. The x402
  // client selects the network (eip155:*) from the server's 402 requirements,
  // so we don't pin a single chain here.
  const walletClient = createWalletClient({
    account: addr as `0x${string}`,
    chain: baseSepolia,
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
