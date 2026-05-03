/**
 * TransparencyDataCarousel.tsx
 *
 * Sprint 17.B — refonte page /transparency.
 *
 * Three "intelligence-grade visualisation screens" presented as a
 * full-width carousel, modeled after the landing page's
 * TransparencyTimeline component (same Carousel primitive, same
 * "classified dossier" framing). Each slide:
 *
 *   - Left  (5 cols)  : an AI-generated screen illustration
 *                       (/api/assets/transparency_<id>.jpg) with a
 *                       CSS-rendered CONFIDENTIEL stamp overlay and
 *                       a DOSSIER tag.
 *   - Right (7 cols)  : the live, MiCA-grade content for that slide
 *                       (BubbleMaps iframe / RugCheck score / Treasury
 *                       operations log table).
 *
 * The carousel itself never owns the live data — it receives ready-
 * to-render React nodes from the parent so we can keep the data
 * fetching co-located with the page (and reuse the existing
 * RugCheckSection / OperationsSection / BubbleMapsSection logic
 * without duplicating it).
 */

import React from "react";
import { motion } from "framer-motion";
import { Network, ShieldCheck, ScrollText, Stamp } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// ---------------------------------------------------------------------
// Slide config
// ---------------------------------------------------------------------
export interface VizSlide {
  /** Stable id used in i18n keys + data-testid. */
  id: "distribution" | "rugcheck" | "operations";
  /** AI-generated illustration filename (without extension). */
  imageSlug: string;
  /** Lucide icon shown next to the dossier tag. */
  // eslint-disable-next-line
  Icon: any;
  /** Dominant accent colour for this slide (matches the AI image tone). */
  accent: string;
  /** Live React content rendered on the right side of the slide. */
  content: React.ReactNode;
}

export const VIZ_SLIDE_DEFAULTS: Pick<
  VizSlide,
  "id" | "imageSlug" | "Icon" | "accent"
>[] = [
  {
    id: "distribution",
    imageSlug: "transparency_distribution",
    Icon: Network,
    accent: "#33FF33", // matrix green — bubble-map nodes
  },
  {
    id: "rugcheck",
    imageSlug: "transparency_rugcheck",
    Icon: ShieldCheck,
    accent: "#2DD4BF", // teal — security shield wireframe
  },
  {
    id: "operations",
    imageSlug: "transparency_operations",
    Icon: ScrollText,
    accent: "#F59E0B", // amber — ledger desk lamp
  },
];

// ---------------------------------------------------------------------
// Slide component
// ---------------------------------------------------------------------
interface VizSlideViewProps {
  slide: VizSlide;
  phaseLabel: string;
  delay: number;
}

const VizSlideView: React.FC<VizSlideViewProps> = ({
  slide,
  phaseLabel,
  delay,
}) => {
  const { t } = useI18n();
  const Icon = slide.Icon;
  const heroUrl = `${BACKEND_URL}/api/assets/${slide.imageSlug}.jpg`;

  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay }}
      className="relative h-full rounded-2xl border border-border bg-card shadow-[var(--shadow-elev-2)] overflow-hidden"
      data-testid={`transparency-viz-slide-${slide.id}`}
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 min-h-[520px]">
        {/* ---- Left: visualisation screen illustration ---- */}
        <div className="lg:col-span-5 relative viz-screen-frame overflow-hidden min-h-[280px] lg:min-h-0">
          <div
            aria-hidden
            className="absolute inset-0 bg-cover bg-center"
            style={{ backgroundImage: `url(${heroUrl})` }}
          />
          {/* Right-edge fade so the right column reads cleanly */}
          <div
            aria-hidden
            className="absolute inset-0 pointer-events-none"
            style={{
              background:
                "linear-gradient(90deg, rgba(0,0,0,0) 55%, rgba(11,13,16,0.78) 100%)",
            }}
          />
          {/* CONFIDENTIEL stamp — pure CSS, guaranteed typo-free */}
          <div
            aria-hidden
            className="absolute top-5 right-5 select-none pointer-events-none"
            style={{ transform: "rotate(-10deg)" }}
          >
            <div className="confidential-stamp">
              <span>CONFIDENTIEL</span>
              <span className="confidential-stamp__sub">
                PROTOCOL ΔΣ · NIVEAU 04
              </span>
            </div>
          </div>
          {/* Dossier tag bottom-left */}
          <div className="absolute bottom-4 left-4 z-10">
            <div className="inline-flex items-center gap-2 bg-[#0B0D10]/85 backdrop-blur px-3 py-1.5 rounded-md border border-foreground/20">
              <Icon size={13} style={{ color: slide.accent }} />
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-foreground/85">
                DOSSIER {phaseLabel}
              </span>
            </div>
          </div>
        </div>

        {/* ---- Right: live structured content ---- */}
        <div className="lg:col-span-7 p-6 md:p-7 lg:p-8 flex flex-col">
          <div className="flex items-center justify-between gap-2 mb-3">
            <span className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              {t(`transparencyPage.viz.${slide.id}.kicker`) as string}
            </span>
            <Stamp size={14} style={{ color: slide.accent }} />
          </div>

          <h3 className="font-display font-semibold text-2xl md:text-3xl leading-tight">
            {t(`transparencyPage.viz.${slide.id}.title`) as string}
          </h3>

          <p className="mt-3 text-sm text-foreground/75 leading-relaxed max-w-prose">
            {t(`transparencyPage.viz.${slide.id}.description`) as string}
          </p>

          {/* The live data slot */}
          <div className="mt-6 flex-1">{slide.content}</div>

          <div className="mt-5 pt-5 border-t border-border/60 flex items-center justify-between gap-3">
            <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
              {t("transparency.signedBy") || "Signé · DEEP STATE COMMITTEE"}
            </span>
            <span
              className="font-mono text-[10px] uppercase tracking-[0.25em]"
              style={{ color: slide.accent }}
            >
              {t("transparency.classified") || "CLASSIFIED"}
            </span>
          </div>
        </div>
      </div>
    </motion.article>
  );
};

// ---------------------------------------------------------------------
// Carousel wrapper
// ---------------------------------------------------------------------
interface TransparencyDataCarouselProps {
  slides: VizSlide[];
}

export const TransparencyDataCarousel: React.FC<
  TransparencyDataCarouselProps
> = ({ slides }) => {
  const { t } = useI18n();

  return (
    <section
      className="mt-12"
      data-testid="transparency-data-carousel"
    >
      {/* ---- Section header — same typographic system as Tokenomics ---- */}
      <div className="mb-6">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("transparencyPage.viz.sectionKicker") as string}
        </div>
        <h2 className="mt-2 font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
          {t("transparencyPage.viz.sectionTitle") as string}
        </h2>
        <p className="mt-3 text-foreground/75 leading-relaxed max-w-2xl text-sm md:text-[15px]">
          {t("transparencyPage.viz.sectionSubtitle") as string}
        </p>
      </div>

      {/* ---- Full-width carousel ---- */}
      <div className="relative -mx-4 sm:-mx-6 md:mx-0">
        <Carousel
          opts={{ align: "start", loop: false }}
          className="w-full"
        >
          <CarouselContent className="px-4 sm:px-6 md:px-0 -ml-4">
            {slides.map((slide, i) => {
              const phaseLabel = `${String(i + 1).padStart(2, "0")} / ${String(slides.length).padStart(2, "0")}`;
              return (
                <CarouselItem
                  key={slide.id}
                  className="pl-4 basis-full md:basis-[95%] lg:basis-full"
                >
                  <VizSlideView
                    slide={slide}
                    phaseLabel={phaseLabel}
                    delay={i * 0.06}
                  />
                </CarouselItem>
              );
            })}
          </CarouselContent>

          {/* ---- Navigation row ---- */}
          <div className="px-4 sm:px-6 md:px-0 mt-5 flex items-center justify-between gap-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              ←{" "}
              {(t("transparencyPage.viz.scrollHint") as string) ||
                "FAITES DÉFILER LES ÉCRANS"}{" "}
              →
            </div>
            <div className="flex items-center gap-2">
              <CarouselPrevious
                className="static translate-y-0 rounded-md border-foreground/40 hover:bg-foreground/5"
                data-testid="transparency-viz-carousel-prev"
              />
              <CarouselNext
                className="static translate-y-0 rounded-md border-foreground/40 hover:bg-foreground/5"
                data-testid="transparency-viz-carousel-next"
              />
            </div>
          </div>
        </Carousel>
      </div>
    </section>
  );
};

export default TransparencyDataCarousel;
