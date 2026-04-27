import React from "react";
import { motion } from "framer-motion";
import { Check, ShieldCheck } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

export default function Mission() {
  const { t } = useI18n();
  const items = t("mission.checklist") || [];

  return (
    <section
      id="mission"
      data-testid="mission-section"
      className="py-14 sm:py-18 lg:py-24 border-t border-border"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-7"
          >
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              {t("mission.kicker")}
            </div>
            <h2 className="mt-3 font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
              {t("mission.title")}
            </h2>
            <p className="mt-5 text-lg text-foreground/85 max-w-2xl">
              {t("mission.lead")}
            </p>
            <p className="mt-4 text-foreground/75 max-w-2xl leading-relaxed">
              {t("mission.body")}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-5"
          >
            <div className="rounded-xl border border-border bg-card p-5 md:p-6 shadow-[var(--shadow-elev-1)]">
              <div className="flex items-center gap-2 mb-4">
                <ShieldCheck size={16} className="text-[#18C964]" />
                <div className="font-display font-semibold">
                  {t("mission.checklistTitle")}
                </div>
              </div>
              <ul className="space-y-4">
                {items.map((it, i) => (
                  <li
                    key={`mission-${i}-${(it?.label || "").slice(0, 20)}`}
                    className="flex items-start gap-3"
                  >
                    <span className="mt-0.5 flex-none w-5 h-5 rounded-full bg-[#18C964]/15 text-[#18C964] flex items-center justify-center">
                      <Check size={12} />
                    </span>
                    <div>
                      <div className="font-medium text-foreground">
                        {it.label}
                      </div>
                      <div className="text-sm text-foreground/70 mt-0.5">
                        {it.detail}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
