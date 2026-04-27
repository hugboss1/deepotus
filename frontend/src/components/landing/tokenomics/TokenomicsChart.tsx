import { motion } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { ShieldCheck, ExternalLink } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import {
  TEAM_LOCK_URL,
  TREASURY_LOCK_URL,
  hasTeamLock,
  hasTreasuryLock,
  hasAnyLock,
} from "@/lib/links";

// eslint-disable-next-line
function CustomTooltip({ active, payload }: any) {
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

/**
 * Left column of the Tokenomics section.
 *
 * Renders:
 *   - the donut pie chart (Recharts) with the gold coin stamped inside
 *   - the "Total supply" pill
 *   - the Jupiter Lock badge (with optional team/treasury proof links)
 *
 * Hover highlights are driven by the parent via `activeKey`.
 */
export function TokenomicsChart({ data, activeKey }) {
  const { t } = useI18n();
  const teamLocked = hasTeamLock();
  const treasuryLocked = hasTreasuryLock();
  const anyLocked = hasAnyLock();

  return (
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
                  opacity={activeKey && activeKey !== d.key ? 0.35 : 1}
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
  );
}

export default TokenomicsChart;
