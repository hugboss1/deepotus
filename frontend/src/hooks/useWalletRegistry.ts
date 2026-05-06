/**
 * useWalletRegistry — Sprint Transparency & Trust.
 *
 * Hydrates the public wallet registry from the backend (Mongo) and
 * falls back to the legacy Vercel env vars when the request fails or
 * a slot is empty. Used by /transparency to render the live, operator-
 * editable wallet table + the RugCheck button.
 *
 * Contract:
 *   * Synchronous on first render (returns env-var fallback so the
 *     SSR/hydration mismatch never flashes).
 *   * `useEffect` then fires a single GET /api/transparency/wallets
 *     and replaces the snapshot on success.
 *   * 30s revalidation interval so an admin who edits a slot sees the
 *     change without forcing a hard refresh on every visitor.
 *   * Failure path is silent — we keep showing the env-var fallback.
 *     The Transparency page never breaks because the registry is
 *     down.
 */
import { useEffect, useState } from "react";
import axios from "axios";

import { getWallets, hasMint } from "@/lib/launchPhase";
import { logger } from "@/lib/logger";

const API: string = process.env.REACT_APP_BACKEND_URL || "";

export interface RegistryWallet {
  id: "deployer" | "treasury" | "team" | "creator_fees" | "community";
  address: string;
  lock_url: string;
  label: string;
}

export interface WalletRegistrySnapshot {
  wallets: RegistryWallet[];
  mint_address: string;
  mint_live: boolean;
  rugcheck_url: string;
  /** True iff the snapshot was hydrated from the backend (vs the env-var fallback). */
  hydrated: boolean;
}

/** Build the env-var-only baseline so first paint is non-empty. */
function buildEnvFallback(): WalletRegistrySnapshot {
  const envWallets = getWallets();
  const envMintAddr = process.env.REACT_APP_DEEPOTUS_MINT || "";
  return {
    wallets: envWallets.map((w) => ({
      id: w.id,
      address: w.address,
      lock_url: w.lockUrl,
      label: "",
    })),
    mint_address: envMintAddr,
    mint_live: hasMint(),
    rugcheck_url: envMintAddr ? `https://rugcheck.xyz/tokens/${envMintAddr}` : "",
    hydrated: false,
  };
}

interface ApiResponse {
  wallets: RegistryWallet[];
  mint_address: string;
  mint_live: boolean;
  rugcheck_url: string;
}

export function useWalletRegistry(): WalletRegistrySnapshot {
  const [snapshot, setSnapshot] = useState<WalletRegistrySnapshot>(() => buildEnvFallback());

  useEffect(() => {
    let cancelled = false;

    const fetchOnce = async (): Promise<void> => {
      try {
        const r = await axios.get<ApiResponse>(`${API}/api/transparency/wallets`);
        if (cancelled) return;
        // Merge: if the backend returns an empty address for a slot,
        // fall back to the env var so devnet / pre-prod environments
        // that haven't seeded the registry yet still see *something*.
        const envFallback = buildEnvFallback();
        const merged = r.data.wallets.map((w): RegistryWallet => {
          const fromEnv = envFallback.wallets.find((e) => e.id === w.id);
          return {
            id: w.id,
            address: w.address || fromEnv?.address || "",
            lock_url: w.lock_url || fromEnv?.lock_url || "",
            label: w.label || "",
          };
        });
        const mintAddr = r.data.mint_address || envFallback.mint_address;
        setSnapshot({
          wallets: merged,
          mint_address: mintAddr,
          mint_live: Boolean(mintAddr),
          rugcheck_url: mintAddr ? `https://rugcheck.xyz/tokens/${mintAddr}` : "",
          hydrated: true,
        });
      } catch (err) {
        // Silent failure — env-var fallback already on screen.
        logger.warn("[wallet-registry] fetch failed, using env fallback", err);
      }
    };

    fetchOnce();
    // 30s revalidation — cheap (single GET, no auth) and keeps the
    // public page in sync if the operator edits a slot mid-session.
    const id = window.setInterval(fetchOnce, 30_000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  return snapshot;
}
