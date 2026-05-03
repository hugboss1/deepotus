/**
 * DisclaimerMarquee — endless scrolling deep-state risk banner.
 *
 * Replaces the previous static red disclaimer block with a CSS-animated
 * marquee. The animation is defined in src/index.css under
 * `@keyframes deepotus-marquee` and the `.animate-marquee` utility class.
 *
 * Implementation notes:
 *  - The track is duplicated *twice* in the DOM (aria-hidden on the second
 *    pass) and the keyframe translates by -50%, which produces a perfectly
 *    seamless loop regardless of viewport width.
 *  - Hovering the banner pauses the animation (CSS) so the user can read.
 *  - `prefers-reduced-motion: reduce` halts the animation (CSS).
 *  - We surface the long-form risk paragraph below as small print so the
 *    MiCA-style disclosure stays readable for compliance.
 */
import { ShieldAlert } from "lucide-react";

const DOT = "·";

export function DisclaimerMarquee({ t }: { t: (key: string) => any }) {
  const messages: string[] = t("roi.marqueeMessages") || [];
  const longRisk = t("roi.risk");

  // Build the rolling track content from the messages array, joined by a
  // monospace separator. We render it twice so the keyframe (-50%) loops.
  const track = (
    <div className="inline-flex items-center gap-6 px-6 font-mono text-[11px] uppercase tracking-[0.2em]">
      {messages.map((m: string, i: number) => (
        <span key={`m-${i}`} className="flex items-center gap-6 text-[#FECACA]">
          <ShieldAlert
            size={11}
            className="text-[#E11D48] shrink-0"
            aria-hidden
          />
          <span>{m}</span>
          <span aria-hidden className="text-white/30">
            {DOT}
          </span>
        </span>
      ))}
    </div>
  );

  return (
    <div
      className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8"
      data-testid="roi-disclaimer-marquee"
    >
      {/* Outer banner — sits flush across the section. */}
      <div
        className="relative overflow-hidden rounded-xl border border-[#E11D48]/40 bg-gradient-to-r from-[#1B0410] via-[#3B0612] to-[#1B0410] shadow-[inset_0_0_0_1px_rgba(225,29,72,0.08)]"
        role="alert"
        aria-label="Risk disclaimer"
      >
        {/* Side fades to soften the marquee edges */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 left-0 w-12 z-10"
          style={{
            background:
              "linear-gradient(90deg, rgba(11,13,16,0.95), rgba(11,13,16,0))",
          }}
        />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 right-0 w-12 z-10"
          style={{
            background:
              "linear-gradient(270deg, rgba(11,13,16,0.95), rgba(11,13,16,0))",
          }}
        />

        <div className="relative py-3 overflow-hidden">
          <div
            className="flex w-max animate-marquee"
            style={{ willChange: "transform" }}
          >
            {track}
            <div aria-hidden>{track}</div>
          </div>
        </div>
      </div>

      {/* Compliance fine print preserved below the rolling banner */}
      <p className="mt-4 text-[11px] md:text-xs text-white/55 leading-relaxed font-mono max-w-3xl">
        <span className="uppercase tracking-widest text-[#E11D48] font-semibold">
          {t("roi.riskTitle")} —
        </span>{" "}
        {longRisk}
      </p>
    </div>
  );
}
