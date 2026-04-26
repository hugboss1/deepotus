// Single source of truth for ROI Simulator constants.
// Pulled into both `synthPath.js` (chart data) and `ROISimulator.jsx` (UI).
export const LAUNCH_PRICE_EUR = 0.0005;
export const TOTAL_SUPPLY = 1_000_000_000; // 1B tokens

// Scenario keys & their default multipliers — kept in sync with the
// `roi.scenarios` block in src/i18n/translations.js. Multipliers must
// match so the chart's endpoint = the calculator card's number.
export const SCENARIO_KEYS = ["brutal", "base", "optimistic"];

export const SCENARIO_COLORS = {
  brutal: "#E11D48", // campaign red
  base: "#F59E0B", // amber
  optimistic: "#18C964", // terminal green
  portfolio: "#2DD4BF", // ocean teal
};

export const CHART_DAYS = 90; // 3-month projection window
