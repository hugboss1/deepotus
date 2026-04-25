// Allocation table — single source of truth shared between the chart and the
// legend. `lockable` flags categories that will be publicly locked via
// Jupiter Lock at launch (team + treasury).
export const ALLOCATIONS = [
  { key: "treasury", value: 30, color: "#2DD4BF", lockable: true },
  { key: "airdrops", value: 20, color: "#E11D48", lockable: false },
  { key: "team", value: 15, color: "#0B0D10", lockable: true },
  { key: "liquidity", value: 15, color: "#33FF33", lockable: false },
  { key: "marketing", value: 10, color: "#F59E0B", lockable: false },
  { key: "ai_lore", value: 10, color: "#16A34A", lockable: false },
];
