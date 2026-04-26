/**
 * PriceChart — interactive Recharts visualisation for the ROI Simulator.
 *
 * Inputs (props):
 *   - t          : i18n translator (already memoised by the parent)
 *   - data       : output of buildChartDataset({ days, tokensHeld, activeKey })
 *                  → array of { day, brutal, base, optimistic, portfolio, ... }
 *   - activeKey  : "brutal" | "base" | "optimistic" — which scenario is in
 *                  focus, used to thicken the matching line and surface its
 *                  values in the tooltip in priority.
 *   - tokensHeld : the user-held token count (>0 toggles the portfolio line).
 *
 * The chart is purely visual — all data shaping happens upstream so this
 * component can stay declarative and fast to re-render.
 */
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { LAUNCH_PRICE_EUR, SCENARIO_COLORS, TOTAL_SUPPLY } from "./constants";

const fmtPrice = (v) => {
  if (v == null || Number.isNaN(v)) return "—";
  if (v >= 1) return `€${v.toFixed(2)}`;
  if (v >= 0.01) return `€${v.toFixed(3)}`;
  return `€${v.toFixed(5)}`;
};

const fmtCompact = (v) => {
  if (v == null || Number.isNaN(v)) return "—";
  return new Intl.NumberFormat(undefined, {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(v);
};

function ChartTooltip({ active, payload, label, t, activeKey, tokensHeld }) {
  if (!active || !payload?.length) return null;

  const byKey = Object.fromEntries(
    payload.map((p) => [p.dataKey, p.value]),
  );

  const scenarioLines = ["brutal", "base", "optimistic"].map((key) => {
    const value = byKey[key];
    const color = SCENARIO_COLORS[key];
    const isActive = key === activeKey;
    return {
      key,
      color,
      isActive,
      value,
      label: t(`roi.chartLegend${key.charAt(0).toUpperCase() + key.slice(1)}`),
    };
  });

  const portfolioValue = byKey.portfolio;
  const activePrice = byKey[activeKey];
  const activeMC = activePrice != null ? activePrice * TOTAL_SUPPLY : null;

  return (
    <div
      className="rounded-lg border border-white/15 bg-[#0B0D10]/95 backdrop-blur-md px-3 py-2 shadow-xl text-[11px]"
      data-testid="roi-chart-tooltip"
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/55">
        {t("roi.chartTooltipDay")}
        {label}
      </div>
      <div className="mt-1.5 space-y-1">
        {scenarioLines.map((row) => (
          <div
            key={row.key}
            className="flex items-center gap-2 font-mono"
            style={{
              color: row.isActive ? row.color : "rgba(255,255,255,0.6)",
              fontWeight: row.isActive ? 600 : 400,
            }}
          >
            <span
              aria-hidden
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: row.color }}
            />
            <span className="flex-1">{row.label}</span>
            <span className="tabular">{fmtPrice(row.value)}</span>
          </div>
        ))}
      </div>

      {activeMC != null && (
        <div className="mt-2 pt-2 border-t border-white/10 flex items-center justify-between font-mono text-white/70">
          <span className="uppercase tracking-widest text-[9px]">
            {t("roi.chartTooltipMC")}
          </span>
          <span className="tabular">€{fmtCompact(activeMC)}</span>
        </div>
      )}

      {tokensHeld > 0 && portfolioValue != null && (
        <div className="mt-1 flex items-center justify-between font-mono">
          <span className="uppercase tracking-widest text-[9px] text-white/70">
            {t("roi.chartTooltipPortfolio")}
          </span>
          <span
            className="tabular font-semibold"
            style={{ color: SCENARIO_COLORS.portfolio }}
          >
            €{fmtCompact(portfolioValue)}
          </span>
        </div>
      )}
    </div>
  );
}

function LegendDot({ color, label, active }) {
  return (
    <div
      className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest"
      style={{
        color: active ? color : "rgba(255,255,255,0.55)",
        fontWeight: active ? 600 : 400,
      }}
    >
      <span
        aria-hidden
        className="inline-block h-1.5 w-3 rounded-full"
        style={{ background: color }}
      />
      <span>{label}</span>
    </div>
  );
}

export function PriceChart({ t, data, activeKey, tokensHeld }) {
  const xTicks = [0, 22, 45, 67, 89]; // 5 evenly spaced ticks across 90 days

  return (
    <div
      className="rounded-2xl border border-white/10 bg-[#0B0D10]/85 backdrop-blur-md p-5 md:p-6 shadow-[0_20px_60px_rgba(0,0,0,0.45)] h-full flex flex-col"
      data-testid="roi-price-chart"
    >
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/60">
          CHART.LIVE
        </div>
        <h3 className="mt-1 font-display text-xl md:text-2xl text-white">
          {t("roi.chartTitle")}
        </h3>
        <p className="mt-1 text-xs md:text-sm text-white/65 max-w-xl">
          {t("roi.chartSubtitle")}
        </p>
      </div>

      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1.5">
        {["brutal", "base", "optimistic"].map((key) => (
          <LegendDot
            key={key}
            color={SCENARIO_COLORS[key]}
            label={t(
              `roi.chartLegend${key.charAt(0).toUpperCase() + key.slice(1)}`,
            )}
            active={key === activeKey}
          />
        ))}
        {tokensHeld > 0 && (
          <LegendDot
            color={SCENARIO_COLORS.portfolio}
            label={t("roi.chartLegendPortfolio")}
            active
          />
        )}
      </div>

      <div className="mt-3 flex-1 min-h-[280px] sm:min-h-[320px] lg:min-h-[360px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={data}
            margin={{ top: 8, right: 14, bottom: 8, left: 0 }}
          >
            <defs>
              <linearGradient id="roi-portfolio-fill" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="0%"
                  stopColor={SCENARIO_COLORS.portfolio}
                  stopOpacity={0.35}
                />
                <stop
                  offset="100%"
                  stopColor={SCENARIO_COLORS.portfolio}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>

            <CartesianGrid
              stroke="rgba(255,255,255,0.06)"
              strokeDasharray="3 4"
              vertical={false}
            />
            <XAxis
              dataKey="day"
              ticks={xTicks}
              tickFormatter={(v) => `J+${v}`}
              tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 10 }}
              axisLine={{ stroke: "rgba(255,255,255,0.12)" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={fmtPrice}
              tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 10 }}
              axisLine={{ stroke: "rgba(255,255,255,0.12)" }}
              tickLine={false}
              width={64}
              domain={[0, "auto"]}
            />
            <Tooltip
              cursor={{ stroke: "rgba(255,255,255,0.18)", strokeDasharray: "3 3" }}
              content={
                <ChartTooltip
                  t={t}
                  activeKey={activeKey}
                  tokensHeld={tokensHeld}
                />
              }
            />
            <Legend content={() => null} />

            {/* Brutal scenario */}
            <Line
              type="monotone"
              dataKey="brutal"
              stroke={SCENARIO_COLORS.brutal}
              strokeWidth={activeKey === "brutal" ? 2.4 : 1}
              strokeOpacity={activeKey === "brutal" ? 1 : 0.5}
              dot={false}
              isAnimationActive
              animationDuration={400}
            />
            {/* Base scenario */}
            <Line
              type="monotone"
              dataKey="base"
              stroke={SCENARIO_COLORS.base}
              strokeWidth={activeKey === "base" ? 2.4 : 1}
              strokeOpacity={activeKey === "base" ? 1 : 0.5}
              dot={false}
              isAnimationActive
              animationDuration={400}
            />
            {/* Optimistic scenario */}
            <Line
              type="monotone"
              dataKey="optimistic"
              stroke={SCENARIO_COLORS.optimistic}
              strokeWidth={activeKey === "optimistic" ? 2.4 : 1}
              strokeOpacity={activeKey === "optimistic" ? 1 : 0.5}
              dot={false}
              isAnimationActive
              animationDuration={400}
            />

            {/* Portfolio overlay (only when user enters an amount) */}
            {tokensHeld > 0 && (
              <Area
                type="monotone"
                dataKey="portfolio"
                yAxisId={0}
                stroke="transparent"
                fill="url(#roi-portfolio-fill)"
                isAnimationActive={false}
                hide
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-white/50">
        <span>{t("roi.chartXLabel")}</span>
        <span>
          {t("roi.chartYLabel")} · base = €{LAUNCH_PRICE_EUR.toFixed(4)}
        </span>
      </div>
    </div>
  );
}
