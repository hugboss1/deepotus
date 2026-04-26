/**
 * DeepStateIntro — first-visit intro animation for the $DEEPOTUS landing.
 *
 * Timeline (14 s total):
 *   T+0.0 → 0.6s   PROLOGUE     boot bandeau "PROTOCOL ΔΣ · INITIATING ..."
 *   T+0.6 → 2.5s   TERMINAL 1   top-left   — kernel + tor handshake
 *   T+2.5 → 4.5s   TERMINAL 2   bottom-right — nmap + exploit
 *   T+4.5 → 6.5s   TERMINAL 3   center     — ΔΣ key derivation
 *   T+6.5 → 8.5s   MATRIX RAIN  full-screen backdrop fades in
 *   T+8.5 → 10.5s  TERMINAL 4   top-right  — "ACCÈS AUTORISÉ" + finale lines
 *   T+10.5 → 12.0s GLITCH       RGB split + scanlines + 100ms flash
 *   T+12.0 → 14.0s FADE OUT     terminals + matrix fade, black overlay drops
 *                                landing page is revealed underneath.
 *
 * Skip rules:
 *   - "Skip · ESC" button (bottom-right)
 *   - ESC key
 *   - Click anywhere (outside terminals)
 *   - Auto-skip when prefers-reduced-motion: reduce
 *
 * Cooldown (validated by user):
 *   - localStorage key `deepstate.intro.lastSeenAt`
 *   - replay window: 24h
 *   - bypass via `?intro=force` query param
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { useI18n } from "@/i18n/I18nProvider";
import GlitchOverlay from "./GlitchOverlay";
import MatrixRain from "./MatrixRain";
import TerminalWindow from "./TerminalWindow";
import {
  FINALE_LINE,
  PROLOGUE_LINE,
  SKIP_HINT,
  TERMINAL_1_LINES,
  TERMINAL_2_LINES,
  TERMINAL_3_LINES,
  TERMINAL_4_LINES,
} from "./hackScripts";

const STORAGE_KEY = "deepstate.intro.lastSeenAt";
const COOLDOWN_MS = 24 * 60 * 60 * 1000; // 24h
const TOTAL_MS = 14_000;

// Per-phase activation timestamps (ms). Tweaked to match the 14s budget.
const PHASES = {
  prologue: { start: 0, end: 600 },
  term1: { start: 600, end: 2500 },
  term2: { start: 2500, end: 4500 },
  term3: { start: 4500, end: 6500 },
  matrix: { start: 6500, end: 12_000 },
  term4: { start: 8500, end: 10_500 },
  glitchRGB: { start: 10_500, end: 11_500 },
  glitchFlash: { start: 11_500, end: 11_700 },
  fadeOut: { start: 12_000, end: 14_000 },
};

function shouldShowIntro() {
  // SSR safety
  if (typeof window === "undefined") return false;

  // Force replay via ?intro=force
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get("intro") === "force") return true;
  } catch (_) {
    /* noop */
  }

  // Reduced-motion users skip the intro entirely.
  try {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return false;
    }
  } catch (_) {
    /* noop */
  }

  // 24h cooldown
  try {
    const lastSeenAt = Number(window.localStorage.getItem(STORAGE_KEY) || 0);
    if (Number.isFinite(lastSeenAt) && Date.now() - lastSeenAt < COOLDOWN_MS) {
      return false;
    }
  } catch (_) {
    /* noop (storage blocked) */
  }
  return true;
}

function markIntroSeen() {
  try {
    window.localStorage.setItem(STORAGE_KEY, String(Date.now()));
  } catch (_) {
    /* noop */
  }
}

export default function DeepStateIntro() {
  const { lang } = useI18n();

  // We compute visibility ONCE on mount so toggling localStorage during
  // playback doesn't yank the intro off-screen.
  const [visible, setVisible] = useState(() => shouldShowIntro());
  const [elapsed, setElapsed] = useState(0);
  const [fading, setFading] = useState(false);
  const startRef = useRef(0);
  const tickRef = useRef(0);
  const finishedRef = useRef(false);

  const finish = useMemo(
    () => () => {
      if (finishedRef.current) return;
      finishedRef.current = true;
      cancelAnimationFrame(tickRef.current);
      markIntroSeen();
      setFading(true);
      // Allow the fade to play before unmounting.
      setTimeout(() => setVisible(false), 700);
    },
    [],
  );

  // Timeline driver — single requestAnimationFrame loop.
  useEffect(() => {
    if (!visible) return undefined;

    // Lock body scroll while the intro is playing.
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    startRef.current = performance.now();
    function loop(now) {
      const t = now - startRef.current;
      setElapsed(t);
      if (t >= TOTAL_MS) {
        finish();
        return;
      }
      tickRef.current = requestAnimationFrame(loop);
    }
    tickRef.current = requestAnimationFrame(loop);

    function onKey(e) {
      if (e.key === "Escape" || e.key === " ") {
        e.preventDefault();
        finish();
      }
    }
    window.addEventListener("keydown", onKey);

    return () => {
      cancelAnimationFrame(tickRef.current);
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [visible, finish]);

  if (!visible) return null;

  const showProloguue =
    elapsed >= PHASES.prologue.start && elapsed < PHASES.prologue.end;
  const showT1 =
    elapsed >= PHASES.term1.start && elapsed < PHASES.fadeOut.start;
  const showT2 =
    elapsed >= PHASES.term2.start && elapsed < PHASES.fadeOut.start;
  const showT3 =
    elapsed >= PHASES.term3.start && elapsed < PHASES.fadeOut.start;
  const showT4 =
    elapsed >= PHASES.term4.start && elapsed < PHASES.fadeOut.start;
  const showMatrix =
    elapsed >= PHASES.matrix.start && elapsed < PHASES.fadeOut.end;

  let glitchPhase = "off";
  if (
    elapsed >= PHASES.glitchFlash.start &&
    elapsed < PHASES.glitchFlash.end
  ) {
    glitchPhase = "flash";
  } else if (
    elapsed >= PHASES.glitchRGB.start &&
    elapsed < PHASES.glitchRGB.end
  ) {
    glitchPhase = "rgb";
  }

  const fadeStarted = fading || elapsed >= PHASES.fadeOut.start;
  const fadeProgress = fadeStarted
    ? Math.min(
        1,
        (elapsed - PHASES.fadeOut.start) /
          (PHASES.fadeOut.end - PHASES.fadeOut.start),
      )
    : 0;
  const blackoutOpacity = fadeStarted ? Math.max(0, 1 - fadeProgress) : 1;
  const skipLabel = SKIP_HINT[lang === "en" ? "en" : "fr"];

  return (
    <div
      role="dialog"
      aria-label="Deep State intro animation"
      data-testid="deepstate-intro-root"
      onClick={finish}
      className="fixed inset-0 z-[9999] cursor-pointer overflow-hidden bg-black"
      style={{ opacity: blackoutOpacity }}
    >
      {/* Matrix rain — sits behind the terminals */}
      {showMatrix ? (
        <MatrixRain
          active={!fadeStarted}
          opacity={fadeStarted ? 0 : 0.55}
        />
      ) : null}

      {/* Prologue bandeau */}
      {showProloguue ? (
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex justify-center pointer-events-none">
          <div className="font-mono text-[11px] sm:text-[13px] uppercase tracking-[0.45em] text-[#18C964]">
            {PROLOGUE_LINE}
            <span
              aria-hidden
              className="inline-block w-[7px] h-[12px] align-[-1px] ml-1 bg-[#18C964] motion-safe:animate-pulse"
            />
          </div>
        </div>
      ) : null}

      {/* Terminals */}
      <div className="relative z-20 w-full h-full">
        <TerminalWindow
          title="kernel://deepstate"
          lines={TERMINAL_1_LINES}
          active={showT1}
          testId="intro-terminal-1"
          className="absolute"
          style={{
            top: "8%",
            left: "5%",
            width: "min(380px, 42vw)",
            opacity: showT1 ? 1 : 0,
            transition: "opacity 350ms",
          }}
        />
        <TerminalWindow
          title="recon://nmap"
          lines={TERMINAL_2_LINES}
          active={showT2}
          testId="intro-terminal-2"
          className="absolute"
          style={{
            bottom: "8%",
            right: "5%",
            width: "min(420px, 46vw)",
            opacity: showT2 ? 1 : 0,
            transition: "opacity 350ms",
          }}
        />
        <TerminalWindow
          title="crypto://ΔΣ-handshake"
          lines={TERMINAL_3_LINES}
          active={showT3}
          testId="intro-terminal-3"
          className="absolute"
          style={{
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "min(420px, 80vw)",
            opacity: showT3 ? 1 : 0,
            transition: "opacity 350ms",
          }}
        />
        <TerminalWindow
          title="session://granted"
          lines={TERMINAL_4_LINES}
          active={showT4}
          testId="intro-terminal-4"
          className="absolute"
          style={{
            top: "8%",
            right: "5%",
            width: "min(360px, 42vw)",
            opacity: showT4 ? 1 : 0,
            transition: "opacity 350ms",
          }}
        />
      </div>

      {/* Glitch overlay (top-most) */}
      <GlitchOverlay phase={glitchPhase} finaleText={FINALE_LINE} />

      {/* Skip hint */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          finish();
        }}
        data-testid="deepstate-intro-skip"
        className="absolute bottom-4 right-4 z-40 font-mono text-[10px] uppercase tracking-[0.35em] text-white/60 hover:text-white border border-white/20 hover:border-white/40 rounded px-2.5 py-1 bg-black/40 backdrop-blur-sm transition-colors"
      >
        {skipLabel}
      </button>

      {/* Tiny corner badge — adds presence without crowding */}
      <div className="absolute top-4 left-4 z-40 font-mono text-[10px] uppercase tracking-[0.35em] text-[#E11D48]/85 select-none">
        ⏵ DEEPSTATE.SYS · {Math.min(99, Math.floor((elapsed / TOTAL_MS) * 100))}%
      </div>
    </div>
  );
}
