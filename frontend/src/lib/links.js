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
