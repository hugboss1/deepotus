import { Lock } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import { hasTeamLock, hasTreasuryLock } from "@/lib/links";

/**
 * Right column legend list. Hovering an item lifts `activeKey` to the parent
 * which dims the rest of the donut chart on the left.
 */
export function TokenomicsLegend({ data, activeKey, setActiveKey }) {
  const { t } = useI18n();
  const teamLocked = hasTeamLock();
  const treasuryLocked = hasTreasuryLock();

  return (
    <ul
      className="grid grid-cols-1 sm:grid-cols-2 gap-3"
      data-testid="tokenomics-legend"
    >
      {data.map((d) => {
        const active = activeKey === d.key;
        const lockProven =
          (d.key === "team" && teamLocked) ||
          (d.key === "treasury" && treasuryLocked);
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
                      lockProven
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
  );
}

export default TokenomicsLegend;
