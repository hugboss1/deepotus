/**
 * ProphetPinnedWhisper — pinned, max-visibility "loyalty seed" whisper from
 * the Prophet, placed *immediately after the Hero* on the landing page so
 * every visitor crosses paths with it.
 *
 * Design intent:
 *   - Visual: classified-dossier paper card, soft typewriter cursor on the
 *     signature, subtle scan-line texture, stamp-like classification chip.
 *   - Narrative: hints — without naming the future token — that holders
 *     who keep their $DEEPOTUS will be rewarded "le moment venu". Reads
 *     like a leaked observation rather than a marketing claim.
 *   - Compliance: footnote line below the quote explicitly states "no
 *     contractual promise / not a financial instrument".
 *   - Accessibility: respects `prefers-reduced-motion` (no anim on the
 *     cursor), uses semantic <blockquote>, and keeps a high contrast on
 *     dark backgrounds.
 */
import { motion } from "framer-motion";
import { ShieldCheck, Sparkles } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

export default function ProphetPinnedWhisper() {
  const { t } = useI18n();
  const kicker = t("prophetWhisper.kicker");
  const classification = t("prophetWhisper.classification");
  const quote = t("prophetWhisper.quote");
  const signature = t("prophetWhisper.signature");
  const footnote = t("prophetWhisper.footnote");

  return (
    <section
      id="prophet-whisper"
      data-testid="prophet-pinned-whisper"
      aria-label="Pinned Prophet observation"
      className="relative isolate py-10 sm:py-12 md:py-14 border-t border-b border-border bg-secondary/40"
    >
      {/* Subtle paper-noise backdrop */}
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none opacity-[0.18]"
        style={{
          backgroundImage:
            "radial-gradient(1200px 400px at 20% 30%, rgba(245,158,11,0.08), transparent 60%), radial-gradient(900px 300px at 85% 70%, rgba(45,212,191,0.06), transparent 60%)",
        }}
      />
      {/* Faint scan lines for the deepstate aesthetic */}
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none mix-blend-overlay opacity-[0.10]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.4) 0 1px, transparent 1px 3px)",
        }}
      />

      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.article
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="relative rounded-2xl border border-[#F59E0B]/30 bg-[#0B0D10]/85 backdrop-blur-md shadow-[0_30px_80px_rgba(0,0,0,0.5)] p-6 sm:p-8 md:p-10 overflow-hidden"
          data-testid="prophet-pinned-whisper-card"
        >
          {/* Top corner ribbon — classification stamp */}
          <div
            aria-hidden
            className="absolute -top-px right-4 sm:right-6 md:right-8 px-2.5 py-1 rounded-b-md bg-[#E11D48]/15 border border-t-0 border-[#E11D48]/40 font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.25em] text-[#FECACA]"
            data-testid="prophet-pinned-classification"
          >
            <ShieldCheck size={10} className="inline -mt-0.5 mr-1" />
            {classification}
          </div>

          {/* Kicker (eyebrow) — small file label */}
          <div className="font-mono text-[10px] sm:text-[11px] uppercase tracking-[0.28em] text-[#F59E0B] flex items-center gap-2">
            <Sparkles size={11} className="opacity-80" aria-hidden />
            <span>{kicker}</span>
          </div>

          {/* The actual whisper — large, readable, blockquote-styled */}
          <blockquote className="mt-4 sm:mt-5">
            <p
              className="font-display text-xl sm:text-2xl md:text-3xl lg:text-[2.25rem] leading-snug text-white"
              data-testid="prophet-pinned-quote"
            >
              <span
                aria-hidden
                className="text-[#F59E0B] mr-1 select-none font-display"
              >
                “
              </span>
              {quote}
              <span
                aria-hidden
                className="text-[#F59E0B] ml-1 select-none font-display"
              >
                ”
              </span>
            </p>

            <footer className="mt-5 sm:mt-6 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span
                className="font-mono text-[11px] sm:text-xs uppercase tracking-[0.25em] text-white/85"
                data-testid="prophet-pinned-signature"
              >
                {signature}
              </span>
              {/* Blinking caret to suggest "still transmitting" */}
              <span
                aria-hidden
                className="inline-block h-3.5 w-[2px] bg-[#2DD4BF] motion-safe:animate-pulse"
              />
            </footer>
          </blockquote>

          {/* Compliance footnote */}
          <p
            className="mt-5 sm:mt-6 max-w-3xl text-[10.5px] sm:text-xs leading-relaxed text-white/55 font-mono"
            data-testid="prophet-pinned-footnote"
          >
            {footnote}
          </p>
        </motion.article>
      </div>
    </section>
  );
}
