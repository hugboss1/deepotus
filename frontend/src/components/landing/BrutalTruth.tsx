import React from "react";
import { motion } from "framer-motion";
import { useI18n } from "@/i18n/I18nProvider";

export default function BrutalTruth() {
  const { t } = useI18n();
  const stats = t("truth.stats") || [];

  return (
    <section
      id="truth"
      data-testid="brutal-truth-section"
      className="relative py-14 sm:py-18 lg:py-24 border-t border-border bg-[#0B0D10] text-zinc-100 overflow-hidden"
    >
      <div
        aria-hidden
        className="absolute inset-0 opacity-[var(--noise-opacity)]"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/></filter><rect width='120' height='120' filter='url(%23n)' opacity='0.35'/></svg>\")",
        }}
      />
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-zinc-500">
          {t("truth.kicker")}
        </div>
        <h2 className="mt-2 font-display text-3xl md:text-5xl lg:text-6xl font-semibold leading-[1.05] text-white">
          {t("truth.title")}
        </h2>
        <p className="mt-3 text-zinc-400 max-w-2xl">{t("truth.subtitle")}</p>

        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-5">
          {stats.map((s: any, i: number) => (
            <motion.div
              key={`brutal-${i}-${(s?.label || "").slice(0, 16)}`}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              data-testid={`brutal-truth-stat-${i}`}
              className="relative rounded-xl border border-zinc-800 bg-gradient-to-b from-[#0e141b] to-[#070a0f] p-6 scanlines"
            >
              <div className="absolute top-3 right-3 font-mono text-[10px] uppercase tracking-widest text-[#E11D48]">
                ● BRUTAL
              </div>
              <div
                className="font-display tabular font-bold leading-none text-white"
                style={{ fontSize: "clamp(44px, 7vw, 88px)" }}
              >
                {s.value}
              </div>
              <div className="mt-2 text-zinc-200 font-medium">{s.label}</div>
              <div className="mt-1 text-xs text-zinc-500 font-mono">
                SRC: {s.source}
              </div>
            </motion.div>
          ))}
        </div>

        <p className="mt-8 text-zinc-300 max-w-3xl italic">« {t("truth.caption")} »</p>
      </div>
    </section>
  );
}
