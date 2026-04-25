import React from "react";
import { motion } from "framer-motion";
import { useI18n } from "@/i18n/I18nProvider";

export default function Manifesto() {
  const { t } = useI18n();
  const body = t("manifesto.body") || [];
  return (
    <section
      id="manifesto"
      data-testid="manifesto-section"
      className="py-14 sm:py-18 lg:py-24 border-t border-border"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              {t("manifesto.kicker")}
            </div>
            <div className="mt-4 font-mono text-xs text-muted-foreground">
              {t("manifesto.prophecyId")} : 0xDEEP…PR0PH3T
            </div>
          </div>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-8"
          >
            <h2 className="font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight text-foreground max-w-3xl">
              {t("manifesto.title")}
            </h2>
            <div className="mt-6 space-y-5 text-foreground/80 max-w-prose">
              {Array.isArray(body) &&
                body.map((p, i) => (
                  <p
                    key={`manifesto-${i}-${(p || "").slice(0, 16)}`}
                    className="leading-relaxed text-base md:text-[17px]"
                  >
                    {p}
                  </p>
                ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
