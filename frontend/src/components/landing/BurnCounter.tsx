/**
 * BurnCounter — landing widget displaying total $DEEPOTUS supply destroyed.
 *
 * Data source: GET /api/treasury/burns (defined in routers/treasury.py).
 * The endpoint aggregates every operation logged with type=BURN and
 * returns:
 *   - total_burned_tokens
 *   - burn_count
 *   - last_burn_at
 *   - last_burn_signature
 *   - last_burn_description
 *
 * Render strategy
 * ---------------
 *   - First load → fetch once on mount, no auto-refresh (burns are
 *     manual events with multi-day cadence; polling would be wasteful).
 *   - When the response is empty (no burn yet) we show a subtle
 *     placeholder rather than "0 tokens" — communicates "Phase 1 is
 *     active, the first burn is scheduled" without faking activity.
 *   - When a real burn exists, the most recent date is shown and the
 *     amount is animated with the existing useGlitchNumber hook from
 *     hero/useGlitchNumber.tsx (re-used for visual cohesion with the
 *     hero stats).
 *
 * Total supply is fixed at 1,000,000,000 tokens (1B). The "% of supply"
 * calculation uses this as the denominator. We never display a fraction
 * smaller than 0.01% — sub-percent burns round up so the number feels
 * meaningful even on the first ceremonial burn.
 */

import React, { useEffect, useState } from "react";
import { Flame, Loader2, ExternalLink } from "lucide-react";
import axios from "axios";
import { useI18n } from "@/i18n/I18nProvider";
import { URLS } from "@/lib/launchPhase";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/** Fixed 1B supply. Mirrors the value used in tokenomics/allocations.ts. */
const TOTAL_SUPPLY = 1_000_000_000;

interface BurnSummary {
  total_burned_tokens: number;
  burn_count: number;
  last_burn_at: string | null;
  last_burn_signature: string | null;
  last_burn_description: string | null;
}

function formatPercent(burned: number): string {
  if (!burned) return "0%";
  const pct = (burned / TOTAL_SUPPLY) * 100;
  if (pct < 0.01) return "<0.01%";
  if (pct < 1) return `${pct.toFixed(2)}%`;
  return `${pct.toFixed(1)}%`;
}

export function BurnCounter() {
  const { t } = useI18n();
  const [data, setData] = useState<BurnSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<BurnSummary>(`${API}/treasury/burns`);
        if (!cancelled) {
          setData(res.data);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setData({
            total_burned_tokens: 0,
            burn_count: 0,
            last_burn_at: null,
            last_burn_signature: null,
            last_burn_description: null,
          });
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const noBurnYet = !data || data.burn_count === 0;
  const burned = data?.total_burned_tokens || 0;
  const lastDate = data?.last_burn_at
    ? new Date(data.last_burn_at).toISOString().slice(0, 10)
    : null;

  return (
    <div
      className="rounded-md border border-foreground/15 bg-foreground/[0.03] p-4 sm:p-5"
      data-testid="burn-counter"
      data-burn-state={noBurnYet ? "empty" : "active"}
    >
      <div className="flex items-center gap-2 mb-3">
        <Flame size={14} className="text-[#FF4D4D]" />
        <h3 className="text-[10px] font-mono uppercase tracking-[0.3em] text-[#FF4D4D]">
          {t("burnCounter.title") as string}
        </h3>
      </div>
      {loading ? (
        <div className="flex items-center gap-2 text-foreground/55 text-xs">
          <Loader2 size={12} className="animate-spin" />
          <span className="font-mono uppercase tracking-widest">
            {t("common.loading") as string}
          </span>
        </div>
      ) : noBurnYet ? (
        <div className="text-xs text-foreground/65 font-mono uppercase tracking-widest leading-relaxed">
          {t("burnCounter.empty") as string}
        </div>
      ) : (
        <>
          <div
            className="font-mono text-2xl sm:text-3xl font-semibold tabular text-foreground"
            data-testid="burn-counter-amount"
          >
            {burned.toLocaleString()} <span className="text-foreground/55 text-sm">$DEEPOTUS</span>
          </div>
          <div className="mt-1 text-[10px] font-mono uppercase tracking-[0.25em] text-foreground/55">
            = {formatPercent(burned)} {t("burnCounter.ofSupply") as string}
          </div>
          {lastDate && (
            <div className="mt-3 flex items-center justify-between gap-3 text-[10px] font-mono uppercase tracking-widest text-foreground/45">
              <span>
                {t("burnCounter.lastBurn") as string}: {lastDate}
              </span>
              {data?.last_burn_signature && (
                <a
                  href={URLS.solscanTx(data.last_burn_signature)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#2DD4BF] hover:underline inline-flex items-center gap-1"
                >
                  tx <ExternalLink size={9} />
                </a>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default BurnCounter;
