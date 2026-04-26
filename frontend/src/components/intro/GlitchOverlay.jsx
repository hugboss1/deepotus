/**
 * GlitchOverlay — full-screen glitch + flash + chromatic-aberration
 * overlay used in the climactic phase of DeepStateIntro.
 *
 * Pure CSS animation defined in src/index.css:
 *   - .deepstate-glitch-rgb (RGB-split + jitter)
 *   - .deepstate-scanlines  (faint scanline texture)
 *   - .deepstate-glitch-flash (white flash spike)
 *
 * This component just toggles those classes on/off based on the `phase`
 * prop so the parent timeline stays in one place.
 */

export default function GlitchOverlay({ phase = "off", finaleText = "" }) {
  if (phase === "off") return null;

  return (
    <div
      aria-hidden
      data-testid="intro-glitch-overlay"
      className="pointer-events-none absolute inset-0 z-30"
    >
      {/* Scanline texture — always on during glitch */}
      <div className="absolute inset-0 deepstate-scanlines opacity-60" />

      {/* RGB-split splash text */}
      {phase === "rgb" || phase === "flash" ? (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative">
            <div className="deepstate-glitch-rgb font-display text-3xl sm:text-5xl md:text-6xl font-semibold uppercase tracking-[0.2em] text-white">
              {finaleText}
            </div>
          </div>
        </div>
      ) : null}

      {/* White flash spike */}
      {phase === "flash" ? (
        <div className="absolute inset-0 deepstate-glitch-flash bg-white" />
      ) : null}
    </div>
  );
}
