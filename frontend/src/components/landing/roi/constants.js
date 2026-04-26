// Single source of truth for ROI Simulator constants.
// Pulled into both `synthPath.js` (chart data) and `ROISimulator.jsx` (UI).

export const TOTAL_SUPPLY = 1_000_000_000; // 1B tokens (fixe)

// --- Prix de référence ---
// 1. Au mint Pump.fun, la bonding curve démarre extrêmement bas.
//    On choisit une valeur "plancher" symbolique avant l'injection founder.
export const MINT_PRICE_EUR = 0.0000005;

// 2. Quelques heures après le mint, le founder injecte 2 000€ de liquidité.
//    Le prix de référence post-injection = capital injecté / total supply.
export const FOUNDER_INJECTION_EUR = 2000;
export const INJECTION_PRICE_EUR = FOUNDER_INJECTION_EUR / TOTAL_SUPPLY; // = €0.000002

// 3. Prix "public" utilisé par le calculateur ROI = prix post-injection
//    (c'est la première fenêtre où les holders peuvent réellement acheter).
export const LAUNCH_PRICE_EUR = INJECTION_PRICE_EUR;

// 4. Cible MiCA / FDV €500k pour le scénario optimiste.
export const TARGET_PRICE_EUR = 0.0005;

// Scénarios — multipliers appliqués au prix d'injection (€0.000002).
//   brutal     → 0.1   = €0.0000002 (≈ -90% / FDV €200)
//   base       → 25    = €0.00005   (FDV ≈ €50k)
//   optimistic → 250   = €0.0005    (FDV €500k = cible MiCA explicite)
export const SCENARIO_KEYS = ["brutal", "base", "optimistic"];

export const SCENARIO_MULTIPLIERS = {
  brutal: 0.1,
  base: 25,
  optimistic: 250,
};

export const SCENARIO_COLORS = {
  brutal: "#E11D48", // campaign red
  base: "#F59E0B", // amber
  optimistic: "#18C964", // terminal green
  portfolio: "#2DD4BF", // ocean teal
};

// --- Roadmap markers (corrélés à la section "The AI Candidate Campaign") ---
// Les jours sont théoriques — le but est de donner une grille de lecture
// aux investisseurs sans promettre de dates fermes. La roadmap publique
// reste "no date promised".
export const ROADMAP_MARKERS = [
  { day: 0, key: "phase01", color: "#18C964", short: "Δ01" },
  { day: 4, key: "phase02", color: "#06B6D4", short: "Δ02" },
  { day: 30, key: "phase03", color: "#F59E0B", short: "Δ03" },
  { day: 75, key: "phase04", color: "#E11D48", short: "Δ04" },
];

// L'injection founder se produit sur le tout début (~3-4h post-mint).
// Sur l'axe 90j, on la place à ~J0.15 pour qu'elle soit lisible.
export const FOUNDER_INJECTION_DAY = 0.15;

export const CHART_DAYS = 90; // 3-month projection window
