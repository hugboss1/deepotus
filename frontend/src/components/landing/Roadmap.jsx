import React from "react";
import { motion } from "framer-motion";
import { Rocket, Layers, Banknote, Flag } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

const ICONS = [Rocket, Layers, Banknote, Flag];

export default function Roadmap() {
  const { t } = useI18n();
  const phases = t("roadmap.phases") || [];

  return (
    <section
      id="roadmap"
      data-testid="roadmap-section"
      className="py-14 sm:py-18 lg:py-24 border-t border-border"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("roadmap.kicker")}
        </div>
        <h2 className="mt-2 font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
          {t("roadmap.title")}
        </h2>

        <div className="relative mt-10">
          {/* Horizontal thin line desktop */}
          <div
            aria-hidden
            className="hidden md:block absolute top-[72px] left-0 right-0 h-px bg-border"
          />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {phases.map((p, i) => {
              const Icon = ICONS[i] || Rocket;
              return (
                <motion.div
                  key={`phase-${p.tag || i}-${(p.title || "").slice(0, 16)}`}
                  initial={{ opacity: 0, y: 14 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-60px" }}
                  transition={{ duration: 0.5, delay: i * 0.05 }}
                  className="relative"
                  data-testid={`roadmap-phase-${i}`}
                >
                  <div className="flex flex-col items-start">
                    <div className="w-12 h-12 rounded-xl bg-background border-2 border-foreground flex items-center justify-center">
                      <Icon size={18} />
                    </div>
                    <div className="mt-3 font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                      {p.tag}
                    </div>
                    <div className="mt-1 font-display font-semibold text-lg">
                      {p.title}
                    </div>
                    <ul className="mt-3 space-y-2 text-sm text-foreground/80">
                      {(p.bullets || []).map((b, j) => (
                        <li key={`${p.tag || i}-bullet-${j}-${(b || "").slice(0, 12)}`} className="flex gap-2">
                          <span className="text-accent font-mono mt-0.5">›</span>
                          <span className="leading-snug">{b}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
