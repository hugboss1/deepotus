/**
 * Synthetic price-path generator for the ROI Simulator chart.
 *
 * Goal: produce a *deterministic* but plausibly chaotic memecoin-style
 * price curve from launch (day 0, €0.0005) to a target multiplier
 * applied at the end of the window, so the chart feels alive and
 * different per scenario without being random across renders.
 *
 * Design notes:
 *  - mulberry32 PRNG: tiny, fast, seedable, distribution good enough.
 *  - the trend is shaped by an ease-out cubic so the bulk of the move
 *    happens early (typical memecoin pump pattern); the noise envelope
 *    decays later (post-pump cooling) — both feel realistic.
 *  - the target price is hit at exactly day = (days - 1) so axis labels
 *    line up cleanly.
 */

import { TOTAL_SUPPLY, LAUNCH_PRICE_EUR } from "./constants";

function mulberry32(seed) {
  let t = seed >>> 0;
  return function () {
    t |= 0;
    t = (t + 0x6d2b79f5) | 0;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function easeOutCubic(x) {
  return 1 - Math.pow(1 - x, 3);
}

/**
 * Generate `days` daily price points for a single scenario.
 *
 * @param {number} multiplier  end-of-window target multiplier (e.g. 0.2, 1, 5)
 * @param {number} days        number of points (default 90)
 * @param {number} seed        RNG seed — different per scenario for variety
 */
export function buildPricePath({ multiplier, days = 90, seed = 1 }) {
  const targetPrice = LAUNCH_PRICE_EUR * multiplier;
  const rng = mulberry32(seed);
  const points = [];

  let lastPrice = LAUNCH_PRICE_EUR;

  for (let d = 0; d < days; d++) {
    const progress = d / (days - 1);
    // Smooth interpolation toward the target along an ease-out cubic.
    const trend =
      LAUNCH_PRICE_EUR + (targetPrice - LAUNCH_PRICE_EUR) * easeOutCubic(progress);

    // Volatility envelope: large early, decays smoothly after the pump.
    // Scaled relative to *current* trend so up-only scenarios swing more
    // in absolute terms (matches memecoin lived experience).
    const envelope =
      trend * 0.18 * (1 - progress) + LAUNCH_PRICE_EUR * 0.04 * progress;
    const noise = (rng() - 0.5) * envelope;

    // Slight momentum so successive days correlate — looks less hairy.
    const momentum = (lastPrice - trend) * 0.12;

    let price = trend + noise - momentum;
    if (price < LAUNCH_PRICE_EUR * 0.05) {
      price = LAUNCH_PRICE_EUR * 0.05; // soft floor (95% drawdown)
    }
    lastPrice = price;

    points.push({
      day: d,
      price,
      marketCap: price * TOTAL_SUPPLY,
    });
  }

  // Snap exact endpoint to the target so the line ends cleanly on the
  // multiplier the user selected (no surprise visual mismatch).
  points[points.length - 1].price = targetPrice;
  points[points.length - 1].marketCap = targetPrice * TOTAL_SUPPLY;

  return points;
}

/**
 * Build the merged dataset that Recharts ingests — one row per day with
 * the three scenario prices PLUS an optional portfolio overlay derived
 * from the active scenario's price path × the user-held tokens.
 *
 * Recharts likes a "wide" shape for multi-line: { day, brutal, base, optimistic, portfolio }
 */
export function buildChartDataset({ days = 90, tokensHeld = 0, activeKey }) {
  const brutal = buildPricePath({ multiplier: 0.2, days, seed: 11 });
  const base = buildPricePath({ multiplier: 1, days, seed: 23 });
  const optimistic = buildPricePath({ multiplier: 5, days, seed: 47 });

  const activePath =
    activeKey === "brutal"
      ? brutal
      : activeKey === "optimistic"
        ? optimistic
        : base;

  return brutal.map((b, i) => ({
    day: b.day,
    brutal: b.price,
    base: base[i].price,
    optimistic: optimistic[i].price,
    activeMarketCap: activePath[i].marketCap,
    activePrice: activePath[i].price,
    portfolio: tokensHeld > 0 ? activePath[i].price * tokensHeld : null,
  }));
}
