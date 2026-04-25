import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Separator } from "@/components/ui/separator";
import { useI18n } from "@/i18n/I18nProvider";
import { isMintConfigured } from "@/lib/links";
import { HeroCountdown } from "./HeroCountdown";

/**
 * Right column poster — auto-cycles through the AI-generated hero variants
 * (paused on hover), exposes a dot pagination, and embeds the dual-state
 * countdown block at the bottom.
 *
 * Self-contained — owns the variant cycle state and the hover-pause flag.
 */
export const HERO_VARIANTS = [
  { src: "/deepotus_hero_serious.jpg", label: "SERIOUS" },
  { src: "/deepotus_hero_meme.jpg", label: "MEME" },
  { src: "/deepotus_hero_glitch.jpg", label: "GLITCH" },
  { src: "/logo_v4_matrix_face.png", label: "MATRIX PROPHET" },
];
const CYCLE_MS = 5000;

export function HeroPoster() {
  const { t } = useI18n();
  const [variantIdx, setVariantIdx] = useState(0);
  const [paused, setPaused] = useState(false);

  // Preload all variants so the cycle is jank-free.
  useEffect(() => {
    HERO_VARIANTS.forEach((v) => {
      const img = new window.Image();
      img.src = v.src;
    });
  }, []);

  // Auto-cycle through variants (respects prefers-reduced-motion + hover pause).
  useEffect(() => {
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    )?.matches;
    if (paused || reduceMotion) return;
    const id = setInterval(() => {
      setVariantIdx((i) => (i + 1) % HERO_VARIANTS.length);
    }, CYCLE_MS);
    return () => clearInterval(id);
  }, [paused]);

  const currentVariant = HERO_VARIANTS[variantIdx];
  const mintLive = isMintConfigured();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.1 }}
      className="lg:col-span-5 order-1 lg:order-2"
    >
      <div
        className="relative bg-card border border-border rounded-xl shadow-[var(--shadow-elev-2)] overflow-hidden scanlines noise"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
        data-testid="hero-poster"
      >
        <div className="relative aspect-[4/5] w-full bg-[#0b1117]">
          <AnimatePresence mode="sync">
            <motion.img
              key={currentVariant.src}
              src={currentVariant.src}
              alt="AI Prophet Deep State Candidate"
              initial={{ opacity: 0, scale: 1.02 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.9, ease: "easeInOut" }}
              className="absolute inset-0 w-full h-full object-cover poster-img"
              loading="eager"
              draggable={false}
              onError={(e) => {
                e.currentTarget.src = "/deepotus_hero.jpg";
              }}
            />
          </AnimatePresence>
          {/* Stamps overlayed on the image (top corners) */}
          <div className="absolute top-3 left-3 z-10">
            <div className="glitch-stamp" data-text={"AI-GENERATED"}>
              AI-GENERATED
            </div>
          </div>
          <div className="absolute top-3 right-3 z-10">
            <div
              className="glitch-stamp"
              data-text={currentVariant.label}
              data-testid="hero-variant-label"
            >
              {currentVariant.label}
            </div>
          </div>
          <div
            aria-hidden
            className="absolute inset-0 pointer-events-none"
            style={{
              background:
                "linear-gradient(180deg, rgba(0,0,0,0.0) 55%, rgba(14,20,27,0.75) 100%)",
            }}
          />
          <div className="absolute left-4 bottom-4 right-4 z-10 pointer-events-none">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#33ff33]">
              &gt; CANDIDATE.LOG
            </div>
            <div className="font-display text-white text-lg leading-tight mt-1">
              {t("hero.ticker")} · {t("hero.chips.chain")}
            </div>
          </div>
        </div>

        {/* Variant pagination dots */}
        <div className="flex items-center justify-center gap-2 py-2 bg-[#0b1117] border-t border-[#1f2937]">
          {HERO_VARIANTS.map((v, i) => {
            const active = i === variantIdx;
            return (
              <button
                key={v.src}
                type="button"
                aria-label={`Show variant ${v.label}`}
                data-testid={`hero-variant-dot-${i}`}
                onClick={() => setVariantIdx(i)}
                className={`h-2 rounded-full transition-all ${
                  active
                    ? "w-6 bg-[#33ff33]"
                    : "w-2 bg-zinc-600 hover:bg-zinc-400"
                }`}
              />
            );
          })}
        </div>

        <Separator />

        <HeroCountdown mintLive={mintLive} />
      </div>
    </motion.div>
  );
}

export default HeroPoster;
