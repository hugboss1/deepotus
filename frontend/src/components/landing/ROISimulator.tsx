/**
 * ROI Simulator — interactive price-trajectory simulator.
 *
 * Composition:
 *  - <CalculatorPanel />   left column — exposes the same "how much are
 *                          you investing?" input + scenario tabs as before.
 *                          State lifted up so the chart can react live.
 *  - <PriceChart />        right column — interactive Recharts LineChart
 *                          plotting brutal/base/optimistic synthetic price
 *                          paths since the mint, plus an overlay of the
 *                          user's portfolio value when an amount is set.
 *  - <DisclaimerMarquee /> bottom — endless scrolling deep-state banner
 *                          replacing the previous static red panel.
 *
 * The base business logic (amount → tokens → multiplier × amount) is
 * preserved exactly. We only add the chart visualisation around it.
 */
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, ShieldAlert } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useI18n } from "@/i18n/I18nProvider";
import {
  FADE_UP_14_INITIAL,
  FADE_UP_ANIMATE,
  FADE_UP_TRANSITION_ROI,
  VIEWPORT_ONCE_M60,
} from "@/lib/motionVariants";
import {
  CHART_DAYS,
  LAUNCH_PRICE_EUR,
  SCENARIO_COLORS,
  SCENARIO_KEYS,
  SCENARIO_MULTIPLIERS,
} from "./roi/constants";
import { buildChartDataset } from "./roi/synthPath";
import { PriceChart } from "./roi/PriceChart";
import { DisclaimerMarquee } from "./roi/DisclaimerMarquee";

// Price formatter that gracefully degrades into scientific notation for the
// sub-fractional memecoin prices we now deal with (€0.000002 etc.).
const fmtRefPrice = (v: number) => {
  if (v >= 0.0001) return v.toFixed(6);
  return v.toExponential(2);
};

export default function ROISimulator() {
  const { t, lang } = useI18n();
  const scenarios = useMemo(() => t("roi.scenarios") || {}, [t]);
  const pricePerToken = LAUNCH_PRICE_EUR;
  const [amount, setAmount] = useState(500);
  const [active, setActive] = useState("base");

  // Currency symbol — sourced from the active locale dictionary so prices
  // displayed in the simulator render in € for FR and $ for EN.
  const currencySymbol = (t("roi.currencySymbol") || (lang === "en" ? "$" : "€"));

  const tokens = useMemo(() => {
    const n = Number(amount);
    if (!Number.isFinite(n) || n <= 0) return 0;
    return Math.floor(n / pricePerToken);
  }, [amount, pricePerToken]);

  const fmt = (n: number) =>
    new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(n);

  const valueFromMultiplier = (mult: number) => tokens * pricePerToken * mult;

  // The chart consumes a single merged dataset re-computed when the user's
  // tokens or active tab change. With CHART_DAYS=90 this is < 1ms and the
  // useMemo guards against re-renders triggered by unrelated state.
  const chartData = useMemo(
    () =>
      buildChartDataset({
        days: CHART_DAYS,
        tokensHeld: tokens,
        activeKey: active,
      }),
    [tokens, active],
  );

  return (
    <section
      id="roi"
      data-testid="roi-section"
      className="relative py-14 sm:py-18 lg:py-24 border-t border-border overflow-hidden bg-secondary/40"
    >
      {/* --- Background: gold coin backdrop, kept from the previous design --- */}
      <div
        aria-hidden
        className="absolute inset-0 z-0 pointer-events-none select-none"
      >
        <img
          src="/gold_coin_3d.png"
          alt=""
          className="h-full w-full object-cover object-center opacity-90 select-none"
          draggable={false}
          loading="lazy"
          decoding="async"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(11,13,16,0.85) 0%, rgba(11,13,16,0.78) 45%, rgba(11,13,16,0.88) 100%)",
          }}
        />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center md:text-left">
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-[#F59E0B]">
            <ShieldAlert size={11} className="inline -mt-0.5 mr-1" />
            {t("roi.kicker")}
          </div>
          <h2 className="mt-2 font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight text-white">
            {t("roi.title")}
          </h2>
          <p className="mt-3 text-sm md:text-base text-white/75 max-w-2xl">
            {t("roi.subtitle")}
          </p>
        </div>

        {/* --- Two-column layout: calculator left, live chart right --- */}
        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-stretch">
          <CalculatorPanel
            t={t}
            scenarios={scenarios}
            amount={amount}
            setAmount={setAmount}
            tokens={tokens}
            active={active}
            setActive={setActive}
            valueFromMultiplier={valueFromMultiplier}
            fmt={fmt}
            currencySymbol={currencySymbol}
          />

          <motion.div
            initial={FADE_UP_14_INITIAL}
            whileInView={FADE_UP_ANIMATE}
            viewport={VIEWPORT_ONCE_M60}
            transition={FADE_UP_TRANSITION_ROI}
            className="lg:col-span-7"
          >
            <PriceChart
              t={t}
              data={chartData}
              activeKey={active}
              tokensHeld={tokens}
              currencySymbol={currencySymbol}
            />
          </motion.div>
        </div>
      </div>

      {/* Bottom-of-section: rolling deep-state risk banner */}
      <div className="relative z-10 mt-10">
        <DisclaimerMarquee t={t} />
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Calculator panel (left column)
// ---------------------------------------------------------------------------
interface CalculatorPanelProps {
  t: (key: string) => any;
  scenarios: Record<string, Record<string, any>>;
  amount: number;
  setAmount: React.Dispatch<React.SetStateAction<number>>;
  tokens: number;
  active: string;
  setActive: (v: string) => void;
  valueFromMultiplier: (mult: number) => number;
  fmt: (n: number) => string;
  currencySymbol: string;
}

function CalculatorPanel({
  t,
  scenarios,
  amount,
  setAmount,
  tokens,
  active,
  setActive,
  valueFromMultiplier,
  fmt,
  currencySymbol,
}: CalculatorPanelProps) {
  return (
    <motion.div
      initial={FADE_UP_14_INITIAL}
      whileInView={FADE_UP_ANIMATE}
      viewport={VIEWPORT_ONCE_M60}
      transition={FADE_UP_TRANSITION_ROI}
      className="lg:col-span-5"
    >
      <div
        className="rounded-2xl border border-white/10 bg-[#0B0D10]/85 backdrop-blur-md p-5 md:p-6 shadow-[0_20px_60px_rgba(0,0,0,0.45)] h-full flex flex-col"
        data-testid="roi-calculator"
      >
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp size={14} className="text-[#2DD4BF]" />
          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/60">
            INPUT.LOG
          </span>
        </div>

        <Label
          htmlFor="roi-amount"
          className="text-sm text-white/85 font-medium"
        >
          {t("roi.amountLabel")}
        </Label>
        <div className="mt-2 relative">
          <span
            aria-hidden
            className="absolute left-3 top-1/2 -translate-y-1/2 text-white/55 font-mono text-sm"
          >
            {currencySymbol}
          </span>
          <Input
            id="roi-amount"
            type="number"
            min="0"
            step="10"
            inputMode="decimal"
            value={amount}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              // Parent stores `amount` as a number; fall back to 0 if empty.
              const v = Number(e.target.value);
              setAmount(Number.isFinite(v) ? v : 0);
            }}
            data-testid="roi-amount-input"
            className="pl-7 font-mono text-lg bg-black/40 border-white/10 text-white placeholder:text-white/30 focus-visible:ring-[#2DD4BF]/50"
          />
        </div>
        <div
          className="mt-2 font-mono text-[11px] text-white/55"
          data-testid="roi-tokens-display"
        >
          ≈ <span className="text-[#2DD4BF]">{fmt(tokens)}</span>{" "}
          $DEEPOTUS · @ {currencySymbol}
          {fmtRefPrice(LAUNCH_PRICE_EUR)}
        </div>

        {/* --- Scenario tabs (existing functionality preserved) --- */}
        <Tabs
          value={active}
          onValueChange={setActive}
          className="mt-5 flex-1 flex flex-col"
        >
          <TabsList
            className="grid grid-cols-3 bg-black/40 border border-white/10 gap-0.5 h-auto"
            data-testid="roi-scenario-tabs"
          >
            {SCENARIO_KEYS.map((key) => (
              <TabsTrigger
                key={key}
                value={key}
                data-testid={`roi-tab-${key}`}
                className="min-w-0 px-1.5 py-2 data-[state=active]:bg-white data-[state=active]:text-[#0B0D10] text-white/70 font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.18em] truncate"
              >
                <span className="truncate">{scenarios[key]?.short || scenarios[key]?.label || key}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          {SCENARIO_KEYS.map((key) => {
            const sc = scenarios[key] || {};
            // Multiplier is sourced from the canonical constants module so
            // the chart endpoint and the calculator card always agree.
            const mult = Number(SCENARIO_MULTIPLIERS[key] ?? sc.multiplier ?? 1);
            const value = valueFromMultiplier(mult);
            const color = SCENARIO_COLORS[key];
            return (
              <TabsContent
                key={key}
                value={key}
                data-testid={`roi-tab-content-${key}`}
                className="mt-4 flex-1"
              >
                <div
                  className="rounded-xl border bg-black/40 p-4 h-full"
                  style={{ borderColor: `${color}55` }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div
                        className="font-mono text-[10px] uppercase tracking-[0.25em]"
                        style={{ color }}
                      >
                        {sc.label || key}
                      </div>
                      <div className="font-display text-2xl md:text-3xl font-semibold text-white tabular mt-0.5">
                        ×{mult.toFixed(mult < 1 ? 2 : 0)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-white/50">
                        {t("roi.resultLabel")}
                      </div>
                      <div
                        className="font-display text-2xl md:text-3xl font-semibold tabular"
                        style={{ color }}
                        data-testid={`roi-result-${key}`}
                      >
                        {currencySymbol}
                        {fmt(value)}
                      </div>
                    </div>
                  </div>
                  <p className="mt-3 text-xs md:text-sm text-white/70 leading-relaxed">
                    {sc.caption || sc.copy}
                  </p>
                </div>
              </TabsContent>
            );
          })}
        </Tabs>
      </div>
    </motion.div>
  );
}
