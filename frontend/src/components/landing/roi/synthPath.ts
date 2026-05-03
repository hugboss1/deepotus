/**
 * Synthetic price-path generator for the ROI Simulator chart.
 *
 * Story modelled by the path:
 *   - day 0           : Pump.fun mint, bonding curve très basse
 *                       (MINT_PRICE_EUR ≈ €0.0000005)
 *   - day 0.15 (~3-4h): Founder injection de 2 000€ → INJECTION_PRICE_EUR
 *                       (€0.000002 = capital ÷ supply 1B)
 *   - day 1 → end     : évolution organique vers le multiplier du scénario
 *                       (×0.1 brutal · ×25 base · ×250 optimistic = €0.0005)
 *
 * The generator is *deterministic* (mulberry32 PRNG) so the chart looks
 * "alive" but reproducible across renders. The trend uses an ease-out cubic
 * (memecoin pump pattern) and a noise envelope that decays over time
 * (post-pump cooling).
 */

import {
  TOTAL_SUPPLY,
  MINT_PRICE_EUR,
  INJECTION_PRICE_EUR,
  FOUNDER_INJECTION_DAY,
  SCENARIO_MULTIPLIERS,
} from "./constants";

function mulberry32(seed: number) {
  let t = seed >>> 0;
  return function () {
    t |= 0;
    t = (t + 0x6d2b79f5) | 0;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function easeOutCubic(x: number) {
  return 1 - Math.pow(1 - x, 3);
}

/**
 * Build a daily price series from the founder injection (J~0.15) to the
 * end of the window, ease-cubic toward `targetPrice`.
 */
function buildOrganicTail({ targetPrice, days, seed }: { targetPrice: number; days: number; seed: number }) {
  const rng = mulberry32(seed);
  const out = [];

  let last = INJECTION_PRICE_EUR;

  // index 0 of this tail represents the first FULL day after injection
  // (i.e. day=1 in the global axis). The last index = days-2 covers day=89.
  const span = days - 1; // we will produce span points (days 1..days-1)

  for (let i = 0; i < span; i++) {
    const progress = i / Math.max(1, span - 1);
    const trend =
      INJECTION_PRICE_EUR +
      (targetPrice - INJECTION_PRICE_EUR) * easeOutCubic(progress);

    // Volatility envelope — large early, decays toward end.
    const envelope =
      trend * 0.22 * (1 - progress) + INJECTION_PRICE_EUR * 0.06 * progress;
    const noise = (rng() - 0.5) * envelope;

    // Soft momentum so consecutive days correlate visually.
    const momentum = (last - trend) * 0.12;

    let price = trend + noise - momentum;
    if (price < INJECTION_PRICE_EUR * 0.05) price = INJECTION_PRICE_EUR * 0.05;
    last = price;

    out.push({ day: i + 1, price, marketCap: price * TOTAL_SUPPLY });
  }

  // Snap exact endpoint to the multiplier so it lines up with the calculator.
  out[out.length - 1].price = targetPrice;
  out[out.length - 1].marketCap = targetPrice * TOTAL_SUPPLY;

  return out;
}

/**
 * Build the full deterministic price path for one scenario, including the
 * mint floor + founder injection visible at the start of the chart.
 */
export function buildPricePath({ multiplier, days = 90, seed = 1 }: { multiplier: number; days?: number; seed?: number }) {
  const targetPrice = INJECTION_PRICE_EUR * multiplier;
  const head = [
    // J0 — mint Pump.fun (bonding curve floor)
    { day: 0, price: MINT_PRICE_EUR, marketCap: MINT_PRICE_EUR * TOTAL_SUPPLY },
    // J~0.15 — founder injection lands. Price snaps to INJECTION_PRICE.
    {
      day: FOUNDER_INJECTION_DAY,
      price: INJECTION_PRICE_EUR,
      marketCap: INJECTION_PRICE_EUR * TOTAL_SUPPLY,
    },
  ];
  const tail = buildOrganicTail({ targetPrice, days, seed });
  return [...head, ...tail];
}

/**
 * Build the merged dataset that Recharts ingests — one row per day with
 * the three scenario prices PLUS an optional portfolio overlay derived
 * from the active scenario's price path × the user-held tokens.
 *
 * Note: the head (J0 + J0.15) is shared across scenarios because mint
 * and injection are deterministic events, not scenario-dependent.
 */
export function buildChartDataset({ days = 90, tokensHeld = 0, activeKey }: { days?: number; tokensHeld?: number; activeKey: string }) {
  const brutal = buildPricePath({
    multiplier: SCENARIO_MULTIPLIERS.brutal,
    days,
    seed: 11,
  });
  const base = buildPricePath({
    multiplier: SCENARIO_MULTIPLIERS.base,
    days,
    seed: 23,
  });
  const optimistic = buildPricePath({
    multiplier: SCENARIO_MULTIPLIERS.optimistic,
    days,
    seed: 47,
  });

  const activePath =
    activeKey === "brutal"
      ? brutal
      : activeKey === "optimistic"
        ? optimistic
        : base;

  // The three arrays have the same length and same "day" axis — merge them.
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
