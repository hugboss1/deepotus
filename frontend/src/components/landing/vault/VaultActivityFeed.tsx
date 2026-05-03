import React, { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Radio } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

interface VaultEvent {
  id: string;
  kind: string;
  agent_code?: string;
  tokens_added: number;
  digits_locked_before: number;
  digits_locked_after: number;
  created_at?: string;
}

/**
 * VaultActivityFeed — scrolling list of recent crack events.
 * Events are already sorted (most recent first) by the backend.
 */
export default function VaultActivityFeed({ events = [] }: { events?: VaultEvent[] }) {
  const { t, lang } = useI18n();

  const rel = (iso?: string) => {
    if (!iso) return "—";
    try {
      const then = new Date(iso).getTime();
      const now = Date.now();
      const delta = Math.max(0, Math.round((now - then) / 1000));
      if (delta < 60) return `${delta}s`;
      if (delta < 3600) return `${Math.round(delta / 60)}m`;
      if (delta < 86400) return `${Math.round(delta / 3600)}h`;
      return `${Math.round(delta / 86400)}d`;
    } catch {
      return "—";
    }
  };

  const kindColor = (k: string) => {
    if (k === "admin_crack") return "text-[#F59E0B]";
    if (k === "purchase") return "text-[#2DD4BF]";
    if (k === "hourly_tick") return "text-muted-foreground";
    if (k === "reset") return "text-red-400";
    return "text-foreground/60";
  };

  const kindLabel = (k: string) => {
    const labels: Record<string, string> = (t("vault.eventKinds") as any) || {};
    return labels[k] || k;
  };

  const items = useMemo(() => events.slice(0, 12), [events]);

  return (
    <div
      className="rounded-xl border border-border bg-card/40 backdrop-blur-sm p-4 md:p-5"
      data-testid="vault-activity-feed"
    >
      <div className="flex items-center gap-2 mb-3">
        <Radio size={14} className="text-[#2DD4BF] animate-pulse" />
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("vault.feedTitle")}
        </div>
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        <AnimatePresence initial={false}>
          {items.length === 0 && (
            <div className="text-sm text-muted-foreground font-mono">
              {t("vault.feedEmpty")}
            </div>
          )}
          {items.map((ev) => {
            const progress =
              ev.digits_locked_after > ev.digits_locked_before;
            return (
              <motion.div
                key={ev.id}
                layout
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="flex items-center justify-between gap-3 py-1.5 border-b border-border/50 last:border-0"
                data-testid={`vault-event-${ev.id}`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className={`font-mono text-[10px] uppercase tracking-wider ${kindColor(ev.kind)} shrink-0`}
                  >
                    {kindLabel(ev.kind)}
                  </span>
                  <span className="font-mono text-xs text-foreground/80 truncate">
                    {ev.agent_code}
                  </span>
                  {progress && (
                    <span className="font-mono text-[10px] text-[#18C964] shrink-0">
                      +{ev.digits_locked_after - ev.digits_locked_before}
                      {lang === "fr" ? " cran" : " digit"}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="font-mono text-[10px] text-foreground/70">
                    +{ev.tokens_added.toLocaleString()} $DEEP
                  </span>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {rel(ev.created_at)}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
