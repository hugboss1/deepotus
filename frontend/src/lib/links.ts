/**
 * Centralized outbound links for the $DEEPOTUS project.
 *
 * - Pump.fun URL is configured via REACT_APP_PUMPFUN_URL at build time.
 * - Until the token is deployed, the buy CTA gracefully falls back to the
 *   whitelist section (#whitelist) so we never ship a broken link.
 */

export const PUMPFUN_URL: string = (
  process.env.REACT_APP_PUMPFUN_URL || ""
).trim();

export const PUMPSWAP_URL: string = (
  process.env.REACT_APP_PUMPSWAP_URL || ""
).trim();

// Public Jupiter Lock / Streamflow URLs that prove team & treasury tokens
// are time-locked. Shown as verified badges once configured.
export const TEAM_LOCK_URL: string = (
  process.env.REACT_APP_TEAM_LOCK_URL || ""
).trim();

export const TREASURY_LOCK_URL: string = (
  process.env.REACT_APP_TREASURY_LOCK_URL || ""
).trim();

/**
 * $DEEPOTUS mint address on Solana.
 *
 * - Override at build time via REACT_APP_DEEPOTUS_MINT once the real Pump.fun
 *   mint is known.
 * - Fallback is an obvious PLACEHOLDER address so the UI never ships empty.
 *   The placeholder is NOT a live token — it is visually-valid base58 used to
 *   preview the layout and copy-to-clipboard UX before launch.
 */
export const DEEPOTUS_MINT: string = (
  process.env.REACT_APP_DEEPOTUS_MINT ||
  "7bQQbXz6pKqHzVJEJxVHTDLqAUkBYt3hM8Jd3vKRYQPv"
).trim();

export function isMintConfigured(): boolean {
  return Boolean(process.env.REACT_APP_DEEPOTUS_MINT);
}

export function hasTeamLock(): boolean {
  return Boolean(TEAM_LOCK_URL);
}
export function hasTreasuryLock(): boolean {
  return Boolean(TREASURY_LOCK_URL);
}
export function hasAnyLock(): boolean {
  return hasTeamLock() || hasTreasuryLock();
}

/**
 * Internal route of the immersive Liquidity Pulse mini-app.
 *
 * Every "Buy $DEEP" / BonkBot buy-flow CTA across the marketing site
 * now funnels here instead of bouncing the visitor straight out to
 * Pump.fun / Telegram — the Pulse page is the on-site buy experience
 * and its own CTA forwards to the BonkBot Telegram app. This keeps the
 * funnel on-domain and adds the "wow" transition into the mini-app.
 *
 * NOTE: the BonkBot link *inside* the Pulse page (pages/Pulse.tsx) is
 * intentionally NOT routed here — it remains the real Telegram exit.
 */
export const PULSE_ROUTE = "/pulse";

/**
 * Return the "Buy $DEEPOTUS" destination.
 *
 * Always the internal Pulse route now (single source of truth for the
 * whole site's buy funnel). Pump.fun / PumpSwap URLs remain exported
 * above for non-CTA contexts (informational labels, dexscreener, …).
 */
export function getBuyUrl(): string {
  return PULSE_ROUTE;
}

/**
 * Buy CTAs are now an internal SPA route, never an external tab.
 * Kept as a function so existing callers ({ target, rel } gating)
 * keep working without edits.
 */
export function isBuyUrlExternal(): boolean {
  return false;
}
