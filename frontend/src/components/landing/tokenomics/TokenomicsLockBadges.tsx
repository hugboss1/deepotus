/**
 * TokenomicsLockBadges — visual summary of the 3-bucket lock model.
 *
 * Renders three at-a-glance chips below the existing donut + legend:
 *
 *   ┌──────────┐  ┌──────────┐  ┌──────────┐
 *   │ Public   │  │ Treasury │  │  Team    │
 *   │   55%    │  │   30%    │  │   15%    │
 *   │ Bonding  │  │ 🔒 6mo   │  │ 🔒 6mo   │
 *   │  curve   │  │  cliff   │  │ cliff +  │
 *   │          │  │  (link)  │  │  12mo    │
 *   │          │  │          │  │ (link)   │
 *   └──────────┘  └──────────┘  └──────────┘
 *
 * The lock URL chips become live links to lock.jup.ag the moment the
 * matching env vars are populated; otherwise they show an amber "Lock
 * pending" placeholder so the user understands the lock will be
 * activated post-mint.
 *
 * The component intentionally does NOT touch the existing allocations.ts
 * file — the 6 detailed sub-allocations stay (treasury, airdrops, team,
 * liquidity, marketing, ai_lore) and naturally sum to the 3 buckets:
 *   - Public 55% = airdrops + liquidity + marketing + ai_lore
 *   - Treasury 30% (lockable)
 *   - Team 15%     (lockable)
 *
 * It's also responsible for the "X% locked · 5 wallets transparent"
 * summary line that bridges the section to the standalone /transparency
 * page.
 */

import { Lock, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { useI18n } from "@/i18n/I18nProvider";
import { URLS } from "@/lib/launchPhase";

interface BucketChip {
  id: "public" | "treasury" | "team";
  pct: string;
  lockable: boolean;
  url: string;
}

const BUCKETS: BucketChip[] = [
  { id: "public", pct: "55%", lockable: false, url: "" },
  { id: "treasury", pct: "30%", lockable: true, url: "" }, // url filled at render
  { id: "team", pct: "15%", lockable: true, url: "" },
];

export function TokenomicsLockBadges() {
  const { t } = useI18n();
  // Resolve URLs at render time (env-driven, can flip without source changes).
  const buckets = BUCKETS.map((b) =>
    b.id === "treasury"
      ? { ...b, url: URLS.treasuryLock }
      : b.id === "team"
        ? { ...b, url: URLS.teamLock }
        : b,
  );

  return (
    <div
      className="mt-10 pt-8 border-t border-border/50"
      data-testid="tokenomics-lock-badges"
    >
      <div className="grid grid-cols-3 gap-3 sm:gap-4">
        {buckets.map((b) => {
          const lockState = !b.lockable
            ? "open"
            : b.url
              ? "locked"
              : "pending";

          const stateClass =
            lockState === "locked"
              ? "border-[#33FF33]/40 bg-[#33FF33]/5"
              : lockState === "pending"
                ? "border-[#F59E0B]/40 bg-[#F59E0B]/5"
                : "border-border bg-secondary/40";

          const lockTextClass =
            lockState === "locked"
              ? "text-[#33FF33]"
              : lockState === "pending"
                ? "text-[#F59E0B]"
                : "text-muted-foreground";

          return (
            <div
              key={b.id}
              className={`rounded-lg border p-3 sm:p-4 transition-colors ${stateClass}`}
              data-testid={`tokenomics-bucket-${b.id}`}
            >
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground">
                {t(`tokenomics.buckets.${b.id}.name`) as string}
              </div>
              <div className="mt-1 font-mono text-2xl sm:text-3xl font-semibold tabular">
                {b.pct}
              </div>
              <div
                className={`mt-2 text-[10px] font-mono uppercase tracking-[0.2em] ${lockTextClass} flex items-center gap-1`}
              >
                {b.lockable && <Lock size={10} />}
                {b.lockable
                  ? lockState === "locked"
                    ? (t(`tokenomics.buckets.${b.id}.locked`) as string)
                    : (t("tokenomics.buckets.lockPending") as string)
                  : (t("tokenomics.buckets.public.terms") as string)}
              </div>
              {b.lockable && b.url && (
                <a
                  href={b.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-[0.2em] text-[#2DD4BF] hover:underline"
                  data-testid={`tokenomics-bucket-${b.id}-link`}
                >
                  Lock proof <ExternalLink size={9} />
                </a>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary cross-link to /transparency */}
      <div className="mt-5 text-center">
        <Link
          to="/transparency"
          className="inline-block font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground hover:text-foreground transition-colors"
          data-testid="tokenomics-transparency-link"
        >
          {t("tokenomics.buckets.summary") as string} →
        </Link>
      </div>
    </div>
  );
}

export default TokenomicsLockBadges;
