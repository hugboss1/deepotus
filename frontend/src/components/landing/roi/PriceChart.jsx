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
 * Visual overlays:
 *   - Founder injection ReferenceDot at FOUNDER_INJECTION_DAY (₂000€).
 *   - Roadmap phase markers (4× ReferenceLine with Δ01..Δ04 caps) tied
 *     to the campaign roadmap section. Captions live in a compact legend
 *     below the chart so the chart itself stays readable.
 */
import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  FOUNDER_INJECTION_DAY,
  INJECTION_PRICE_EUR,
  LAUNCH_PRICE_EUR,
  ROADMAP_MARKERS,
  SCENARIO_COLORS,
  TOTAL_SUPPLY,
} from "./constants";

const fmtPrice = (v, sym = "€") => {
  if (v == null || Number.isNaN(v)) return "—";
  if (v >= 1) return `${sym}${v.toFixed(2)}`;
  if (v >= 0.01) return `${sym}${v.toFixed(3)}`;
  if (v >= 0.0001) return `${sym}${v.toFixed(5)}`;
  // Sub-fractional memecoin range — switch to scientific.
  return `${sym}${v.toExponential(2)}`;
};

const fmtCompact = (v) => {
  if (v == null || Number.isNaN(v)) return "—";
  return new Intl.NumberFormat(undefined, {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(v);
};

function ChartTooltip({ active, payload, label, t, activeKey, tokensHeld, currencySymbol }) {
  if (!active || !payload?.length) return null;

  const byKey = Object.fromEntries(payload.map((p) => [p.dataKey, p.value]));

  const scenarioLines = ["brutal", "base", "optimistic"].map((key) => ({
    key,
    color: SCENARIO_COLORS[key],
    isActive: key === activeKey,
    value: byKey[key],
    label: t(`roi.chartLegend${key.charAt(0).toUpperCase() + key.slice(1)}`),
  }));

  const portfolioValue = byKey.portfolio;
  const activePrice = byKey[activeKey];
  const activeMC = activePrice != null ? activePrice * TOTAL_SUPPLY : null;
  const dayLabel = Number(label).toFixed(Number(label) < 1 ? 2 : 0);

  return (
    <div
      className="rounded-lg border border-white/15 bg-[#0B0D10]/95 backdrop-blur-md px-3 py-2 shadow-xl text-[11px]"
      data-testid="roi-chart-tooltip"
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/55">
        {t("roi.chartTooltipDay")}
        {dayLabel}
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
            <span className="tabular">{fmtPrice(row.value, currencySymbol)}</span>
          </div>
        ))}
      </div>

      {activeMC != null && (
        <div className="mt-2 pt-2 border-t border-white/10 flex items-center justify-between font-mono text-white/70">
          <span className="uppercase tracking-widest text-[9px]">
            {t("roi.chartTooltipMC")}
          </span>
          <span className="tabular">{currencySymbol}{fmtCompact(activeMC)}</span>
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
            {currencySymbol}{fmtCompact(portfolioValue)}
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

/**
 * Compact roadmap legend rendered below the chart so the chart itself
 * keeps a clean signal-to-noise ratio. Each cell pairs a coloured Δ tag
 * with its short label coming from i18n (`roi.roadmapPhases.<key>`).
 */
function RoadmapLegend({ t }) {
  const phases = t("roi.roadmapPhases") || {};
  return (
    <div
      className="mt-4 grid grid-cols-2 gap-x-3 gap-y-2.5"
      data-testid="roi-roadmap-legend"
    >
      {ROADMAP_MARKERS.map((m) => {
        const phase = phases[m.key] || {};
        return (
          <div
            key={m.key}
            className="flex items-start gap-2 min-w-0"
            data-testid={`roi-roadmap-legend-${m.key}`}
          >
            <span
              aria-hidden
              className="shrink-0 mt-[2px] inline-flex items-center justify-center rounded-sm border px-1.5 py-[1px] font-mono text-[9px] uppercase tracking-widest"
              style={{
                color: m.color,
                borderColor: `${m.color}66`,
                background: `${m.color}1A`,
              }}
            >
              {m.short}
            </span>
            <div className="min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-widest text-white/85 truncate">
                {phase.title || m.key}
              </div>
              <div className="font-mono text-[9px] text-white/45 truncate">
                {t("roi.roadmapDayPrefix")}
                {m.day}
                {phase.subtitle ? ` · ${phase.subtitle}` : ""}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function PriceChart({ t, data, activeKey, tokensHeld, currencySymbol = "€" }) {
  const xTicks = [0, 22, 45, 67, 89]; // 5 evenly spaced ticks across 90 days
  const amountMasked = t("roi.injectionAmountMasked") || `xxxx${currencySymbol}`;

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

        {/* Deep State Initiation callout — amount is intentionally masked */}
        <div
          className="mt-3 inline-flex items-center gap-2 rounded-md border border-[#2DD4BF]/30 bg-[#2DD4BF]/10 px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-[#2DD4BF]"
          data-testid="roi-injection-callout"
        >
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#2DD4BF]" />
          {t("roi.injectionCallout")} · {amountMasked} →{" "}
          {fmtPrice(INJECTION_PRICE_EUR, currencySymbol)}
        </div>
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

      <div className="mt-3 flex-1 min-h-[300px] sm:min-h-[340px] lg:min-h-[380px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={data}
            margin={{ top: 24, right: 18, bottom: 8, left: 0 }}
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
              type="number"
              domain={[0, 89]}
              ticks={xTicks}
              tickFormatter={(v) => `${t("roi.roadmapDayPrefix") || "J+"}${v}`}
              tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 10 }}
              axisLine={{ stroke: "rgba(255,255,255,0.12)" }}
              tickLine={false}
              allowDecimals={false}
            />
            <YAxis
              tickFormatter={(v) => fmtPrice(v, currencySymbol)}
              tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 10 }}
              axisLine={{ stroke: "rgba(255,255,255,0.12)" }}
              tickLine={false}
              width={78}
              scale="log"
              domain={["auto", "auto"]}
              allowDataOverflow={false}
            />
            <Tooltip
              cursor={{ stroke: "rgba(255,255,255,0.18)", strokeDasharray: "3 3" }}
              content={
                <ChartTooltip
                  t={t}
                  activeKey={activeKey}
                  tokensHeld={tokensHeld}
                  currencySymbol={currencySymbol}
                />
              }
            />
            <Legend content={() => null} />

            {/* --- Roadmap phase markers (Δ01 → Δ04) --- */}
            {ROADMAP_MARKERS.map((m) => (
              <ReferenceLine
                key={`marker-${m.key}`}
                x={m.day}
                stroke={m.color}
                strokeDasharray="4 4"
                strokeOpacity={0.55}
                label={{
                  value: m.short,
                  position: "top",
                  fill: m.color,
                  fontSize: 10,
                  fontFamily: "monospace",
                  fontWeight: 600,
                }}
              />
            ))}

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

            {/* Founder-injection event marker on the active line */}
            <ReferenceDot
              x={FOUNDER_INJECTION_DAY}
              y={INJECTION_PRICE_EUR}
              r={5}
              fill={SCENARIO_COLORS.portfolio}
              stroke="#0B0D10"
              strokeWidth={2}
              ifOverflow="extendDomain"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-white/50">
        <span>{t("roi.chartXLabel")}</span>
        <span>
          {t("roi.chartYLabel")} · ref = {fmtPrice(LAUNCH_PRICE_EUR, currencySymbol)}
        </span>
      </div>

      {/* Roadmap legend — clarifies what each Δ marker stands for */}
      <RoadmapLegend t={t} />
    </div>
  );
}
