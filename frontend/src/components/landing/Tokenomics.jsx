import React, { useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { motion } from "framer-motion";
import { useI18n } from "@/i18n/I18nProvider";

const ALLOCATIONS = [
  { key: "treasury", value: 30, color: "#2DD4BF" },
  { key: "airdrops", value: 20, color: "#E11D48" },
  { key: "team", value: 15, color: "#0B0D10" },
  { key: "liquidity", value: 15, color: "#33FF33" },
  { key: "marketing", value: 10, color: "#F59E0B" },
  { key: "ai_lore", value: 10, color: "#16A34A" },
];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-[var(--shadow-elev-1)]">
      <div className="font-display font-semibold text-foreground">
        {p.label}
      </div>
      <div className="tabular font-mono text-sm text-foreground/80">
        {p.value}%
      </div>
      <div className="text-xs text-foreground/70 mt-1 max-w-[220px]">
        {p.detail}
      </div>
    </div>
  );
}

export default function Tokenomics() {
  const { t } = useI18n();
  const [activeKey, setActiveKey] = useState(null);

  const data = useMemo(() => {
    return ALLOCATIONS.map((a) => ({
      key: a.key,
      value: a.value,
      color: a.color,
      label: t(`tokenomics.categories.${a.key}.name`),
      detail: t(`tokenomics.categories.${a.key}.detail`),
    }));
  }, [t]);

  const tax = t("tokenomics.tax") || [];

  return (
    <section
      id="tokenomics"
      data-testid="tokenomics-chart"
      className="py-14 sm:py-18 lg:py-24 border-t border-border bg-secondary/30"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("tokenomics.kicker")}
        </div>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-3 mt-2">
          <h2 className="font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
            {t("tokenomics.title")}
          </h2>
          <div className="tabular font-mono text-sm text-muted-foreground">
            {t("tokenomics.subtitle")}
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-6 relative"
            data-testid="tokenomics-pie"
          >
            <div className="relative h-[340px] md:h-[420px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="label"
                    innerRadius="55%"
                    outerRadius="85%"
                    paddingAngle={2}
                    stroke="hsl(var(--background))"
                    strokeWidth={2}
                  >
                    {data.map((d) => (
                      <Cell
                        key={d.key}
                        fill={d.color}
                        opacity={
                          activeKey && activeKey !== d.key ? 0.35 : 1
                        }
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              {/* Gold coin stamped at the center of the donut — fills the inner void */}
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <motion.img
                  src="/gold_coin_front.png"
                  alt="$DEEPOTUS · PROTOCOL ΔΣ — frappe officielle"
                  initial={{ opacity: 0, scale: 0.85 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.7, ease: "easeOut", delay: 0.2 }}
                  className="h-[55%] w-[55%] object-contain drop-shadow-[0_10px_28px_rgba(212,175,55,0.35)] select-none"
                  data-testid="tokenomics-coin-center"
                  draggable={false}
                />
              </div>
            </div>

            {/* Total supply — moved below the chart for legibility */}
            <div
              className="mt-4 flex items-center justify-center gap-3 rounded-xl border border-border bg-card/70 px-4 py-3"
              data-testid="tokenomics-total-supply"
            >
              <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                {t("tokenomics.totalLabel")}
              </span>
              <span className="font-display font-semibold text-xl md:text-2xl tabular">
                1B
              </span>
              <span className="text-xs text-muted-foreground tabular hidden sm:inline">
                · 1,000,000,000
              </span>
            </div>
          </motion.div>

          <div className="lg:col-span-6" data-testid="tokenomics-legend">
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {data.map((d) => {
                const active = activeKey === d.key;
                return (
                  <li
                    key={d.key}
                    onMouseEnter={() => setActiveKey(d.key)}
                    onMouseLeave={() => setActiveKey(null)}
                    data-testid={`tokenomics-legend-${d.key}`}
                    className={`rounded-xl border px-4 py-3 cursor-default transition-colors ${
                      active
                        ? "border-foreground bg-card"
                        : "border-border bg-card/70"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <span
                          className="inline-block w-3 h-3 rounded-sm flex-none"
                          style={{ background: d.color }}
                        />
                        <span className="font-medium truncate">{d.label}</span>
                      </div>
                      <span className="tabular font-mono text-sm text-foreground/80">
                        {d.value}%
                      </span>
                    </div>
                    <div className="text-xs text-foreground/70 mt-1 leading-snug">
                      {d.detail}
                    </div>
                  </li>
                );
              })}
            </ul>

            {/* Tax block */}
            <div className="mt-6 rounded-xl border border-border bg-card p-4">
              <div className="font-display font-semibold mb-2">
                {t("tokenomics.taxTitle")} ·{" "}
                <span className="tabular text-accent">3%</span>
              </div>
              <div className="flex gap-2 flex-wrap">
                {tax.map((tx, i) => (
                  <div
                    key={i}
                    className="inline-flex items-center gap-2 text-xs rounded-full border border-border px-3 py-1.5 bg-background"
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: tx.color }}
                    />
                    <span>{tx.label}</span>
                  </div>
                ))}
              </div>
              <div className="text-xs text-muted-foreground mt-2 leading-relaxed">
                {t("tokenomics.taxCap")}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
