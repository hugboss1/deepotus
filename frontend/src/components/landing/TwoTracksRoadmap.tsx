/**
 * TwoTracksRoadmap — Sprint 20 lead-in for the existing Roadmap.
 *
 * Sits ABOVE <Roadmap /> on the landing page to communicate the two
 * parallel narratives:
 *   - Track A (visible products: Roman, Boardgame, VideoGen, Mobile/D&D)
 *   - Track B (secret project, tied to the 5 wallets phases)
 *
 * Sprint 20.2: the previous two static columns of cards were swapped
 * for a single, interactive <TwoTracksGraph /> visualisation (animated
 * SVG nodes + flowing connections + tap-to-detail modal). The header
 * (kicker / title / lead) and footer disclaimer are kept here so the
 * narrative copy stays in one place and the SEO / a11y surface
 * remains identical.
 */
import { motion } from "framer-motion";
import { useI18n } from "@/i18n/I18nProvider";
import { TwoTracksGraph } from "./TwoTracksGraph";

export function TwoTracksRoadmap(): JSX.Element {
  const { t } = useI18n();

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

        {/* Interactive graph (Sprint 20.2) */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.5 }}
          className="mt-10"
        >
          <TwoTracksGraph />
        </motion.div>

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
