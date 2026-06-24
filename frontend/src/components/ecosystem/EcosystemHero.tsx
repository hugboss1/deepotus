/**
 * EcosystemHero — opening section for /ecosysteme.
 *
 * Premium ambient hero: deep navy background, gold typographic accent,
 * a subtle radial light wash echoing the velvet/lamp aesthetic of the
 * product photos. Aligned with the existing brand (Space Grotesk for
 * display, IBM Plex Mono for the kicker, paper-tone CTA).
 */
import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import { cn } from "@/lib/utils";

export function EcosystemHero(): JSX.Element {
  const { t } = useI18n();
  return (
    <section
      id="hero"
      data-testid="ecosystem-hero"
      className="relative overflow-hidden"
    >
      {/* Decorative deep-sea gradient wash. Kept well below 20% of
          the viewport per design rule. */}
      <div
        aria-hidden
        className="absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(60% 60% at 30% 20%, rgba(245,158,11,0.10) 0%, rgba(45,212,191,0.05) 35%, rgba(0,0,0,0) 75%)",
        }}
      />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16 lg:pt-32 lg:pb-24">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-3xl"
        >
          <div
            data-testid="ecosystem-hero-kicker"
            className="font-mono text-[11px] uppercase tracking-[0.32em] text-amber-400/85 mb-5"
          >
            {t("ecosystem.hero.kicker")}
          </div>
          <h1
            data-testid="ecosystem-hero-title"
            className={cn(
              "font-display font-semibold",
              "text-4xl sm:text-5xl lg:text-6xl",
              "leading-[1.05] tracking-tight",
              "text-foreground"
            )}
          >
            {t("ecosystem.hero.title")}
          </h1>
          <p
            data-testid="ecosystem-hero-subtitle"
            className="mt-6 text-base md:text-lg leading-relaxed text-foreground/75 max-w-prose"
          >
            {t("ecosystem.hero.subtitle")}
          </p>
          <a
            href="#roman"
            data-testid="ecosystem-hero-scrollcue"
            className="mt-10 inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.28em] text-foreground/60 hover:text-foreground transition-colors"
          >
            {t("ecosystem.hero.scrollCue")}
            <ChevronDown className="h-4 w-4 animate-bounce" aria-hidden />
          </a>
        </motion.div>
      </div>
    </section>
  );
}
