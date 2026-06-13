/**
 * TwoTracksRoadmap — Sprint 20 lead-in for the existing Roadmap.
 *
 * Sits ABOVE <Roadmap /> on the landing page to communicate the two
 * parallel narratives:
 *   - Track A (visible products: Roman, Boardgame, VideoGen, Mobile/D&D)
 *   - Track B (secret project, tied to the 5 wallets phases)
 *
 * We deliberately do NOT modify the existing <Roadmap /> component
 * (which renders the canonical ΔΣ phases). The component below acts
 * as an introductory two-column block, then the standard timeline
 * provides the canonical phase numbering.
 */
import { motion } from "framer-motion";
import {
  BookOpen,
  Dices,
  Wand2,
  Smartphone,
  Coins,
  Banknote,
  Construction,
  Heart,
  EyeOff,
  Sparkles,
} from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

const TRACK_A_ICONS = [BookOpen, Dices, Wand2, Smartphone];
const TRACK_B_ICONS = [Coins, Banknote, Construction, Heart, EyeOff];

interface TrackStep {
  code: string;
  label: string;
  note: string;
  wallet?: string;
}

export function TwoTracksRoadmap(): JSX.Element {
  const { t } = useI18n();
  // ``t`` returns ``any`` (string | array | object) so we can pull the
  // step arrays directly from the translation tree.
  const trackA = (t("roadmapTracks.trackA.steps") as TrackStep[]) || [];
  const trackB = (t("roadmapTracks.trackB.steps") as TrackStep[]) || [];

  return (
    <section
      id="two-tracks"
      data-testid="two-tracks-roadmap"
      className="relative pt-20 pb-10"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.45 }}
          className="text-left max-w-3xl"
        >
          <div className="font-mono text-[11px] uppercase tracking-[0.32em] text-amber-400/85">
            {t("roadmapTracks.kicker")}
          </div>
          <h2
            className="mt-3 font-display font-semibold text-3xl sm:text-4xl text-foreground tracking-tight"
            data-testid="two-tracks-title"
          >
            {t("roadmapTracks.title")}
          </h2>
          <p className="mt-3 text-sm md:text-base text-foreground/70 leading-relaxed font-body">
            {t("roadmapTracks.lead")}
          </p>
        </motion.div>

        {/* Two parallel tracks */}
        <div className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Track A — Products */}
          <motion.div
            initial={{ opacity: 0, x: -12 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5 }}
            className="rounded-2xl border border-amber-500/30 bg-amber-500/[0.04] p-6 sm:p-7"
            data-testid="track-a-products"
          >
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-300" aria-hidden />
              <div className="font-mono text-[11px] uppercase tracking-[0.28em] text-amber-200/95">
                {t("roadmapTracks.trackA.label")}
              </div>
            </div>
            <div className="mt-3 font-display font-semibold text-xl text-foreground">
              {t("roadmapTracks.trackA.title")}
            </div>
            <ol className="mt-5 space-y-3">
              {trackA.map((step, i) => {
                const Icon = TRACK_A_ICONS[i] || Sparkles;
                return (
                  <li
                    key={step.code}
                    data-testid={`track-a-step-${i}`}
                    className="flex items-start gap-3 rounded-md border border-border/50 bg-background/40 p-3"
                  >
                    <div className="w-9 h-9 shrink-0 rounded-md bg-amber-500/15 border border-amber-500/35 grid place-items-center text-amber-300">
                      <Icon className="h-4 w-4" aria-hidden />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-baseline gap-2">
                        <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-300/85">
                          {step.code}
                        </span>
                        <span className="font-display font-semibold text-foreground text-sm">
                          {step.label}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-foreground/70 leading-relaxed font-body">
                        {step.note}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </motion.div>

          {/* Track B — Secret Project */}
          <motion.div
            initial={{ opacity: 0, x: 12 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5, delay: 0.08 }}
            className="rounded-2xl border border-cyan-500/30 bg-cyan-500/[0.04] p-6 sm:p-7"
            data-testid="track-b-secret"
          >
            <div className="flex items-center gap-2">
              <EyeOff className="h-4 w-4 text-cyan-300" aria-hidden />
              <div className="font-mono text-[11px] uppercase tracking-[0.28em] text-cyan-200/95">
                {t("roadmapTracks.trackB.label")}
              </div>
            </div>
            <div className="mt-3 font-display font-semibold text-xl text-foreground">
              {t("roadmapTracks.trackB.title")}
            </div>
            <ol className="mt-5 space-y-3">
              {trackB.map((step, i) => {
                const Icon = TRACK_B_ICONS[i] || Sparkles;
                return (
                  <li
                    key={step.code}
                    data-testid={`track-b-step-${i}`}
                    className="flex items-start gap-3 rounded-md border border-border/50 bg-background/40 p-3"
                  >
                    <div className="w-9 h-9 shrink-0 rounded-md bg-cyan-500/15 border border-cyan-500/35 grid place-items-center text-cyan-300">
                      <Icon className="h-4 w-4" aria-hidden />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-baseline gap-2 flex-wrap">
                        <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-cyan-300/85">
                          {step.code}
                        </span>
                        <span className="font-display font-semibold text-foreground text-sm">
                          {step.label}
                        </span>
                        {step.wallet && (
                          <span className="font-mono text-[9px] uppercase tracking-[0.20em] rounded-sm px-1.5 py-0.5 bg-cyan-500/12 text-cyan-200 border border-cyan-500/30">
                            · {step.wallet}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-foreground/70 leading-relaxed font-body">
                        {step.note}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </motion.div>
        </div>

        <p
          className="mt-7 text-[11px] text-foreground/55 leading-relaxed font-body italic max-w-3xl"
          data-testid="two-tracks-footer"
        >
          {t("roadmapTracks.footer")}
        </p>
      </div>
    </section>
  );
}
