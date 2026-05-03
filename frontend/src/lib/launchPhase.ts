/**
 * launchPhase.ts — Single source of truth for the deepotus.xyz launch state.
 *
 * Why this file exists
 * --------------------
 * Hero, Tokenomics, HowToBuy, Roadmap, Transparency and the Burn counter
 * all need to render different copy, CTAs, badges and external URLs
 * depending on whether the project is:
 *
 *   - PRE-MINT      : whitelist phase, no token deployed yet
 *   - LIVE          : Pump.fun bonding curve is open, token has a mint
 *   - GRADUATED     : bonding curve cleared $69K MC, PumpSwap pool live
 *
 * Every component must derive its phase via {@link getLaunchPhase} so a
 * single env var change in Vercel (and a redeploy) flips the whole
 * landing page instantly — no source code change required.
 *
 * Phase logic
 * -----------
 *   PUMPSWAP_URL set                 → 'graduated'
 *   MINT set AND PUMPFUN_URL set     → 'live'
 *   otherwise                        → 'pre'
 *
 * The order matters: graduated supersedes live (because once the token
 * has graduated, the bonding curve UI is stale and we want users on
 * PumpSwap), and live supersedes pre.
 *
 * Wallet env vars (5-wallets transparency model)
 * ----------------------------------------------
 *   REACT_APP_WALLET_DEPLOYER         deployer (drained post-launch)
 *   REACT_APP_WALLET_TREASURY         treasury (30%)
 *   REACT_APP_WALLET_TEAM             team (15%, vested)
 *   REACT_APP_WALLET_CREATOR_FEES     creator fees flux
 *   REACT_APP_WALLET_COMMUNITY        community rewards flux
 *
 * They're optional everywhere — components fall back to a "TBD
 * post-mint" placeholder when missing, so the page degrades gracefully
 * during the pre-mint phase.
 */

export type LaunchPhase = "pre" | "live" | "graduated";

const env = (k: string): string => {
  // CRA injects REACT_APP_* at build time on process.env. We tolerate
  // both ``undefined`` and the literal empty string — Vercel users
  // sometimes leave a var "set but empty" when wiring the project,
  // which should be treated identically to missing.
  const v = process.env[k];
  return typeof v === "string" ? v.trim() : "";
};

/**
 * Compute the current phase from the runtime env. Cheap, pure, safe to
 * call on every render. Components should still memo it once at the
 * top of the tree if they pass it down deep.
 */
export function getLaunchPhase(): LaunchPhase {
  if (env("REACT_APP_PUMPSWAP_URL")) return "graduated";
  if (env("REACT_APP_DEEPOTUS_MINT") && env("REACT_APP_PUMPFUN_URL")) {
    return "live";
  }
  return "pre";
}

/**
 * Centralised URL helpers. All the on-chain explorer / aggregator
 * links live here so a future swap (e.g. Solscan → SolanaFM) only
 * touches this file.
 *
 * Functions are used (instead of pre-computed strings) for the URLs
 * that depend on the mint, because the mint can be empty during
 * pre-mint and we want callers to easily check ``URLS.dexscreener()``
 * truthiness.
 */
export const URLS = {
  // Direct buy / trade flows
  pumpfun: env("REACT_APP_PUMPFUN_URL"),
  pumpswap: env("REACT_APP_PUMPSWAP_URL"),
  bonkbot: env("REACT_APP_BONKBOT_REF_URL"),

  // Lock proofs (lock.jup.ag deep links — pre-filled at lock-creation)
  teamLock: env("REACT_APP_TEAM_LOCK_URL"),
  treasuryLock: env("REACT_APP_TREASURY_LOCK_URL"),

  // Mint-derived explorers
  dexscreener: (): string => {
    const m = env("REACT_APP_DEEPOTUS_MINT");
    return m ? `https://dexscreener.com/solana/${m}` : "";
  },
  rugcheck: (): string => {
    const m = env("REACT_APP_DEEPOTUS_MINT");
    return m ? `https://rugcheck.xyz/tokens/${m}` : "";
  },
  rugcheckApi: (): string => {
    const m = env("REACT_APP_DEEPOTUS_MINT");
    return m ? `https://api.rugcheck.xyz/v1/tokens/${m}/report/summary` : "";
  },
  bubblemaps: (): string => {
    const m = env("REACT_APP_DEEPOTUS_MINT");
    return m ? `https://app.bubblemaps.io/sol/token/${m}` : "";
  },
  solscanTx: (sig: string): string =>
    sig ? `https://solscan.io/tx/${sig}` : "",
  solscanWallet: (addr: string): string =>
    addr ? `https://solscan.io/account/${addr}` : "",
};

/**
 * Five-wallets transparency model. Fields are intentionally ``""`` (not
 * null) when the env var is unset so JSX/template strings render an
 * empty string rather than the literal "null" / "undefined". Callers
 * use truthy checks to decide between "show address" and "TBD" badge.
 */
export interface WalletInfo {
  /** Stable id for React keys + i18n lookups. */
  id: "deployer" | "treasury" | "team" | "creator_fees" | "community";
  /** Public wallet address — empty string until set in Vercel. */
  address: string;
  /** Optional lock proof URL (lock.jup.ag) — only meaningful for team/treasury. */
  lockUrl: string;
}

export function getWallets(): WalletInfo[] {
  return [
    {
      id: "deployer",
      address: env("REACT_APP_WALLET_DEPLOYER"),
      lockUrl: "",
    },
    {
      id: "treasury",
      address: env("REACT_APP_WALLET_TREASURY"),
      lockUrl: env("REACT_APP_TREASURY_LOCK_URL"),
    },
    {
      id: "team",
      address: env("REACT_APP_WALLET_TEAM"),
      lockUrl: env("REACT_APP_TEAM_LOCK_URL"),
    },
    {
      id: "creator_fees",
      address: env("REACT_APP_WALLET_CREATOR_FEES"),
      lockUrl: "",
    },
    {
      id: "community",
      address: env("REACT_APP_WALLET_COMMUNITY"),
      lockUrl: "",
    },
  ];
}

/**
 * Optional ISO-8601 launch timestamp used by the Hero countdown in
 * pre-mint phase. Callers should null-coalesce to ``null`` on parse
 * failure so the countdown component can render its "scheduled soon"
 * fallback instead of throwing.
 *
 * Example value (Vercel env):  ``REACT_APP_LAUNCH_TS=2026-06-15T18:00:00Z``
 */
export function getLaunchTimestamp(): Date | null {
  const raw = env("REACT_APP_LAUNCH_TS");
  if (!raw) return null;
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * Convenience flag — ``true`` when the project actually has a mint
 * deployed (live or graduated). Used by Transparency / Tokenomics to
 * decide whether to render the BubbleMaps iframe + RugCheck score.
 */
export function hasMint(): boolean {
  return Boolean(env("REACT_APP_DEEPOTUS_MINT"));
}

/**
 * Convenience accessor — kept separate from ``URLS`` because the raw
 * mint string is sometimes displayed (with copy button) without being
 * wrapped in an explorer URL.
 */
export function getMint(): string {
  return env("REACT_APP_DEEPOTUS_MINT");
}
