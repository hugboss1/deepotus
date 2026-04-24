/**
 * Centralized outbound links for the $DEEPOTUS project.
 *
 * - Pump.fun URL is configured via REACT_APP_PUMPFUN_URL at build time.
 * - Until the token is deployed, the buy CTA gracefully falls back to the
 *   whitelist section (#whitelist) so we never ship a broken link.
 */

export const PUMPFUN_URL = (
  process.env.REACT_APP_PUMPFUN_URL || ""
).trim();

export const RAYDIUM_URL = (
  process.env.REACT_APP_RAYDIUM_URL || ""
).trim();

// Public Jupiter Lock / Streamflow URLs that prove team & treasury tokens
// are time-locked. Shown as verified badges once configured.
export const TEAM_LOCK_URL = (
  process.env.REACT_APP_TEAM_LOCK_URL || ""
).trim();

export const TREASURY_LOCK_URL = (
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
export const DEEPOTUS_MINT = (
  process.env.REACT_APP_DEEPOTUS_MINT ||
  "7bQQbXz6pKqHzVJEJxVHTDLqAUkBYt3hM8Jd3vKRYQPv"
).trim();

export function isMintConfigured() {
  return Boolean(process.env.REACT_APP_DEEPOTUS_MINT);
}

export function hasTeamLock() {
  return Boolean(TEAM_LOCK_URL);
}
export function hasTreasuryLock() {
  return Boolean(TREASURY_LOCK_URL);
}
export function hasAnyLock() {
  return hasTeamLock() || hasTreasuryLock();
}

/**
 * Return the best "Buy $DEEPOTUS" URL.
 *   - Once the mint is live on Pump.fun → link straight to the coin page
 *   - Before launch → anchor to the whitelist/countdown section
 *
 * Opens in a new tab when external.
 */
export function getBuyUrl() {
  if (PUMPFUN_URL) return PUMPFUN_URL;
  if (RAYDIUM_URL) return RAYDIUM_URL;
  return "#whitelist";
}

export function isBuyUrlExternal() {
  return Boolean(PUMPFUN_URL || RAYDIUM_URL);
}
