import React from "react";
import { motion } from "framer-motion";
import { Lock, Sparkles, Shield } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

const ICONS = [Sparkles, Shield, Lock];

export default function TransparencyTimeline() {
  const { t } = useI18n();
  const timeline = t("transparency.timeline") || [];

  return (
    <section
      id="transparency"
      data-testid="transparency-timeline"
      className="py-14 sm:py-18 lg:py-24 border-t border-border"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("transparency.kicker")}
        </div>
        <h2 className="mt-2 font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
          {t("transparency.title")}
        </h2>
        <p className="mt-3 text-foreground/80 max-w-2xl">
          {t("transparency.subtitle")}
        </p>

        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6" data-testid="lp-treasury-timeline">
          {timeline.map((phase, i) => {
            const Icon = ICONS[i] || Sparkles;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                className="relative rounded-xl border border-border bg-card p-5 shadow-[var(--shadow-elev-1)]"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                    PHASE / {phase.phase}
                  </span>
                  <Icon size={16} className="text-accent" />
                </div>
                <div className="font-display font-semibold text-lg">
                  {phase.title}
                </div>
                <ul className="mt-3 space-y-2 text-sm text-foreground/80">
                  {phase.bullets.map((b, j) => (
                    <li key={j} className="flex gap-2">
                      <span className="text-accent font-mono mt-0.5">▪</span>
                      <span className="leading-snug">{b}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            );
          })}
        </div>

        <div className="mt-8 rounded-xl border-2 border-foreground/80 bg-background p-5 md:p-6">
          <div className="font-display font-semibold text-foreground">
            {t("transparency.proofTitle")}
          </div>
          <p className="mt-2 text-foreground/80 leading-relaxed max-w-3xl">
            {t("transparency.proof")}
          </p>
        </div>
      </div>
    </section>
  );
}
