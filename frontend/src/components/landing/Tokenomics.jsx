import React, { useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ShieldCheck, ExternalLink, Lock, Rocket, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import {
  TEAM_LOCK_URL,
  TREASURY_LOCK_URL,
  hasTeamLock,
  hasTreasuryLock,
  hasAnyLock,
  getBuyUrl,
  isBuyUrlExternal,
  PUMPFUN_URL,
} from "@/lib/links";

// Allocations: 30/20/15/15/10/10. `lockable` flags mark categories that will
// be publicly locked via Jupiter Lock at launch (team + treasury).
const ALLOCATIONS = [
  { key: "treasury", value: 30, color: "#2DD4BF", lockable: true },
  { key: "airdrops", value: 20, color: "#E11D48", lockable: false },
  { key: "team", value: 15, color: "#0B0D10", lockable: true },
  { key: "liquidity", value: 15, color: "#33FF33", lockable: false },
  { key: "marketing", value: 10, color: "#F59E0B", lockable: false },
  { key: "ai_lore", value: 10, color: "#16A34A", lockable: false },
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
      lockable: a.lockable,
      label: t(`tokenomics.categories.${a.key}.name`),
      detail: t(`tokenomics.categories.${a.key}.detail`),
    }));
  }, [t]);

  const teamLocked = hasTeamLock();
  const treasuryLocked = hasTreasuryLock();
  const anyLocked = hasAnyLock();

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
                  <Tooltip
                    content={<CustomTooltip />}
                    wrapperStyle={{ zIndex: 50, outline: "none" }}
                  />
                </PieChart>
              </ResponsiveContainer>
              {/* Gold coin stamped at the center of the donut — fills the inner void */}
              <div className="pointer-events-none absolute inset-0 z-0 flex items-center justify-center">
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
                  loading="lazy"
                  decoding="async"
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

            {/* Jupiter Lock Certified badge */}
            <div
              className={`mt-3 rounded-xl border px-4 py-3 flex items-start gap-3 ${
                anyLocked
                  ? "border-[#18C964]/50 bg-[#18C964]/8"
                  : "border-border bg-card/70"
              }`}
              data-testid="tokenomics-lock-badge"
            >
              <div
                className={`mt-0.5 rounded-full p-1.5 ${
                  anyLocked ? "bg-[#18C964]/20" : "bg-muted"
                }`}
              >
                <ShieldCheck
                  size={14}
                  className={anyLocked ? "text-[#18C964]" : "text-muted-foreground"}
                  strokeWidth={2.2}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="font-display font-semibold text-sm">
                    {t("tokenomics.lockBadgeTitle")}
                  </div>
                  <span
                    className={`font-mono text-[9px] uppercase tracking-widest px-2 py-0.5 rounded-full ${
                      anyLocked
                        ? "bg-[#18C964]/15 text-[#18C964] border border-[#18C964]/40"
                        : "bg-muted text-muted-foreground border border-border"
                    }`}
                  >
                    {anyLocked ? "VERIFIED" : "PENDING LAUNCH"}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                  {anyLocked
                    ? t("tokenomics.lockBadgeVerified")
                    : t("tokenomics.lockBadgePending")}
                </p>
                {anyLocked && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {teamLocked && (
                      <a
                        href={TEAM_LOCK_URL}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest text-[#18C964] hover:underline"
                        data-testid="tokenomics-lock-team-cta"
                      >
                        {t("tokenomics.lockTeamLabel")}
                        <ExternalLink size={10} />
                      </a>
                    )}
                    {treasuryLocked && (
                      <a
                        href={TREASURY_LOCK_URL}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest text-[#18C964] hover:underline"
                        data-testid="tokenomics-lock-treasury-cta"
                      >
                        {t("tokenomics.lockTreasuryLabel")}
                        <ExternalLink size={10} />
                      </a>
                    )}
                  </div>
                )}
              </div>
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
                        {d.lockable && (
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-widest shrink-0 ${
                              (d.key === "team" && teamLocked) ||
                              (d.key === "treasury" && treasuryLocked)
                                ? "border border-[#18C964]/50 bg-[#18C964]/10 text-[#18C964]"
                                : "border border-border bg-muted text-muted-foreground"
                            }`}
                            title={t("tokenomics.lockBadgeTitle")}
                            data-testid={`tokenomics-lock-chip-${d.key}`}
                          >
                            <Lock size={9} strokeWidth={2.5} />
                            LOCK
                          </span>
                        )}
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

            {/* 0% Tax Protocol · Cynical Transparency */}
            <div className="mt-6 rounded-xl border-2 border-[#18C964]/40 bg-gradient-to-br from-[#18C964]/5 to-card p-5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-[#18C964]/50 bg-[#18C964]/10 px-2.5 py-1 font-mono text-[10px] uppercase tracking-widest text-[#18C964]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#18C964] animate-pulse" />
                  Pump.fun
                </span>
                <div className="font-display font-semibold text-lg">
                  {t("tokenomics.taxTitle")}
                </div>
                <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {t("tokenomics.taxBadge")}
                </span>
              </div>
              <p className="text-sm text-foreground/85 mt-2 leading-relaxed">
                {t("tokenomics.taxIntro")}
              </p>
              <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                {t("tokenomics.taxCap")}
              </p>

              <div className="mt-4 pt-4 border-t border-[#18C964]/20">
                <div className="font-mono text-[10px] uppercase tracking-widest text-[#18C964] mb-1.5">
                  {t("tokenomics.cynicalTitle")}
                </div>
                <p className="text-sm text-foreground/80 italic leading-relaxed">
                  {t("tokenomics.cynicalBody")}
                </p>
              </div>
            </div>

            {/* Buy $DEEPOTUS — double CTA (guide + direct buy) */}
            <div
              className="mt-6 rounded-xl border border-border bg-card p-5"
              data-testid="tokenomics-buy-cta-block"
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
                {t("tokenomics.buyKicker")}
              </div>
              <h3 className="mt-1 font-display font-semibold text-xl md:text-2xl">
                {t("tokenomics.buyTitle")}
              </h3>
              <p className="mt-2 text-sm text-foreground/80 leading-relaxed">
                {t("tokenomics.buyCopy")}
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <Button
                  asChild
                  size="lg"
                  className="rounded-[var(--btn-radius)] btn-press font-semibold"
                  data-testid="tokenomics-buy-primary"
                >
                  <a
                    href={getBuyUrl()}
                    target={isBuyUrlExternal() ? "_blank" : undefined}
                    rel={isBuyUrlExternal() ? "noopener noreferrer" : undefined}
                  >
                    <Rocket size={16} className="mr-1" />
                    {t("tokenomics.buyCtaPrimary")}
                  </a>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="rounded-[var(--btn-radius)] btn-press font-semibold"
                  data-testid="tokenomics-buy-guide"
                >
                  <Link to="/how-to-buy">
                    <BookOpen size={16} className="mr-1" />
                    {t("tokenomics.buyCtaGuide")}
                  </Link>
                </Button>
              </div>
              {!PUMPFUN_URL && (
                <p className="mt-3 font-mono text-[10px] text-muted-foreground">
                  {t("tokenomics.buyPrelaunchNote")}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
