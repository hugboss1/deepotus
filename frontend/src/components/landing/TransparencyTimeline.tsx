import React from "react";
import { motion } from "framer-motion";
import { Lock, Sparkles, Shield, Stamp } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";

// Static art mapping — stable across re-renders. The illustrations are
// AI-generated "classified contract pages" stored in /public.
const PHASE_VISUALS = [
  {
    image: "/phase_01_launch.png",
    icon: Sparkles,
    accent: "#F59E0B",
  },
  {
    image: "/phase_02_bonding_curve.png",
    icon: Sparkles,
    accent: "#22D3EE",
  },
  {
    image: "/phase_03_pumpswap_migration.png",
    icon: Shield,
    accent: "#E11D48",
  },
  {
    image: "/phase_04_anti_dump.png",
    icon: Lock,
    accent: "#18C964",
  },
];

/**
 * TransparencyTimeline — full-width carousel of the 4 Treasury Discipline
 * phases. Each slide is rendered as a "classified contract page" with a
 * vintage parchment illustration on the left and the structured bullet
 * checklist on the right. The bright red CONFIDENTIEL stamp is overlaid
 * via CSS (NOT rendered into the AI image) — this guarantees zero typos
 * and zero ‘CONFIDENTIAL’ misspellings whatever the diffusion model decides.
 */
export default function TransparencyTimeline() {
  const { t } = useI18n();
  const timeline = t("transparency.timeline") || [];

  return (
    <section
      id="transparency"
      data-testid="transparency-timeline"
      className="py-14 sm:py-18 lg:py-24 border-t border-border overflow-hidden"
    >
      {/* ---- Header ---- */}
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
      </div>

      {/* ---- Full-width carousel ---- */}
      <div
        className="mt-10 relative"
        data-testid="lp-treasury-timeline"
      >
        <Carousel
          opts={{ align: "start", loop: false }}
          className="w-full"
        >
          <CarouselContent className="px-4 sm:px-6 lg:px-12 -ml-4">
            {timeline.map((phase: any, i: number) => {
              const visual = PHASE_VISUALS[i] || PHASE_VISUALS[0];
              const Icon = visual.icon;
              const phaseLabel = `${String(i + 1).padStart(2, "0")} / ${String(timeline.length).padStart(2, "0")}`;
              return (
                <CarouselItem
                  key={phase.phase || i}
                  className="pl-4 basis-full md:basis-[88%] lg:basis-[80%] xl:basis-[72%]"
                >
                  <PhaseSlide
                    phase={phase}
                    phaseLabel={phaseLabel}
                    visual={visual}
                    Icon={Icon}
                    delay={i * 0.04}
                  />
                </CarouselItem>
              );
            })}
          </CarouselContent>

          {/* Navigation buttons — positioned over the carousel */}
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 flex items-center justify-between gap-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              ← {t("transparency.scrollHint") || "FAITES DÉFILER LES DOSSIERS CLASSÉS"} →
            </div>
            <div className="flex items-center gap-2">
              <CarouselPrevious
                className="static translate-y-0 rounded-md border-foreground/40 hover:bg-foreground/5"
                data-testid="transparency-carousel-prev"
              />
              <CarouselNext
                className="static translate-y-0 rounded-md border-foreground/40 hover:bg-foreground/5"
                data-testid="transparency-carousel-next"
              />
            </div>
          </div>
        </Carousel>
      </div>

      {/* ---- Proof card ---- */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-10">
        <div className="rounded-xl border-2 border-foreground/80 bg-background p-5 md:p-6">
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

/* -------------------------------------------------------------------------- */
/*  Slide                                                                     */
/* -------------------------------------------------------------------------- */

// eslint-disable-next-line
function PhaseSlide({ phase, phaseLabel, visual, Icon, delay }: any) {
  const { t } = useI18n();

  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay }}
      className="relative h-full rounded-2xl border border-border bg-card shadow-[var(--shadow-elev-2)] overflow-hidden"
      data-testid={`transparency-slide-${phase.phase || phaseLabel}`}
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 min-h-[420px] md:min-h-[460px]">
        {/* ---- Left: contract illustration with overlaid stamp ---- */}
        <div className="lg:col-span-6 relative bg-[#0B0D10] overflow-hidden">
          {/* Background image */}
          <div
            aria-hidden
            className="absolute inset-0 bg-cover bg-center"
            style={{ backgroundImage: `url(${visual.image})` }}
          />
          {/* Subtle gradient to anchor the right side */}
          <div
            aria-hidden
            className="absolute inset-0 pointer-events-none"
            style={{
              background:
                "linear-gradient(90deg, rgba(0,0,0,0) 60%, rgba(11,13,16,0.85) 100%)",
            }}
          />

          {/* CSS-rendered CONFIDENTIEL stamp — guaranteed typo-free */}
          <div
            aria-hidden
            className="absolute top-6 right-6 select-none pointer-events-none"
            style={{ transform: "rotate(-12deg)" }}
          >
            <div className="confidential-stamp">
              <span>CONFIDENTIEL</span>
              <span className="confidential-stamp__sub">
                PROTOCOL ΔΣ · NIVEAU 04
              </span>
            </div>
          </div>

          {/* Phase index — bottom-left tag */}
          <div className="absolute bottom-4 left-4 z-10">
            <div className="inline-flex items-center gap-2 bg-[#0B0D10]/85 backdrop-blur px-3 py-1.5 rounded-md border border-foreground/20">
              <Icon size={13} style={{ color: visual.accent }} />
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-foreground/80">
                DOSSIER {phaseLabel}
              </span>
            </div>
          </div>
        </div>

        {/* ---- Right: structured contract content ---- */}
        <div className="lg:col-span-6 p-6 md:p-7 lg:p-8 flex flex-col">
          <div className="flex items-center justify-between gap-2 mb-3">
            <span className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              PHASE / {phase.phase}
            </span>
            <Stamp size={14} style={{ color: visual.accent }} />
          </div>

          <h3 className="font-display font-semibold text-2xl md:text-3xl leading-tight">
            {phase.title}
          </h3>

          <ul
            className="mt-5 space-y-3 text-[15px] text-foreground/85"
            data-testid={`transparency-bullets-${phase.phase || phaseLabel}`}
          >
            {(phase.bullets || []).map((b: string) => (
              <li key={b} className="flex gap-2.5 leading-relaxed">
                <span
                  className="font-mono mt-1 shrink-0"
                  style={{ color: visual.accent }}
                  aria-hidden
                >
                  ▪
                </span>
                <span>{b}</span>
              </li>
            ))}
          </ul>

          <div className="mt-auto pt-5 border-t border-border/60 flex items-center justify-between gap-3">
            <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
              {t("transparency.signedBy") || "Signé · DEEP STATE COMMITTEE"}
            </span>
            <span
              className="font-mono text-[10px] uppercase tracking-[0.25em]"
              style={{ color: visual.accent }}
            >
              {t("transparency.classified") || "CLASSIFIED"}
            </span>
          </div>
        </div>
      </div>
    </motion.article>
  );
}
