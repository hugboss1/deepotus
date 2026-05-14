/**
 * /pulse — "The Liquidity Pulse" (Sprint 18).
 *
 * Immersive omnichannel landing optimised for two contexts:
 *  1. Telegram Mini App (TMA) — opens edge-to-edge, ready+expand
 *     called via {@link useTelegramWebApp}.
 *  2. Regular mobile/desktop browser — same experience, minus the
 *     TMA chrome integration.
 *
 * Mechanics:
 *  - Background: animated portrait artwork ($DEEP BUY BOT, octopus
 *    + electric aura) with subtle pulse scale + periodic glitch
 *    (RGB-split clip-band) layered through CSS keyframes.
 *  - Tap interaction: the entire viewport is a tap target. Each tap
 *    spawns a "+X.XX SOL" digital-green float at the click point,
 *    plays a synthesised mechanical-keyboard click, and removes the
 *    float after 1 s. Float pool is capped to MAX_CONCURRENT_FLOATS
 *    to prevent DOM bloat on rapid-fire taps.
 *  - CTA: fixed bottom button that links to BonkBot referral. We
 *    stopPropagation on the button so tapping it doesn't also spawn
 *    a float / play a click.
 *
 * Performance discipline:
 *  - Background image uses <picture> with WebP-first / JPG fallback,
 *    decoding="async", and loading="eager" (it's hero content).
 *  - Floats animate ONLY transform + opacity → composited on GPU,
 *    no reflow.
 *  - Float lifecycle uses a single setTimeout per tap; cleared in
 *    a ref-based pool to handle React StrictMode double-mount.
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ExternalLink,
  FileLock2,
  Lock,
  Megaphone,
  Radar,
  Shield,
  Target,
  Wallet,
  X as XIcon,
  Zap,
} from "lucide-react";

import { useClickSound } from "./pulse/useClickSound";
import { useTelegramWebApp } from "./pulse/useTelegramWebApp";
import {
  MISSIONS,
  GIVEAWAY,
  TELEGRAM_CHANNEL_URL,
  type MissionFamily,
} from "@/lib/missions";
import type { LucideIcon } from "lucide-react";

// ---------------------------------------------------------------------
// Tunables
// ---------------------------------------------------------------------

/** Hard ceiling for simultaneous SOL floats. Rapid-tap stress test
 * with 500ms hold shows ~12 concurrent on a mid-range Android; we
 * cap at 20 with a 60% safety margin. */
const MAX_CONCURRENT_FLOATS = 20;

/** Float lifetime in ms — must match the CSS animation duration. */
const FLOAT_LIFETIME_MS = 1000;

/** Min/max randomised SOL amount displayed per tap. */
const SOL_MIN = 0.1;
const SOL_MAX = 50;

/** BonkBot referral entry point (Sprint 18 spec). */
const BONKBOT_REF_URL = "https://t.me/bonkbot_bot?start=ref_osca5";

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------

interface SolFloat {
  id: number;
  x: number;
  y: number;
  amount: string; // pre-formatted, "+1.23 SOL"
  /** Horizontal drift offset (-30..30 px) so multiple floats from the
   *  same hot-spot don't perfectly overlap. */
  drift: number;
}

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------

function randomSolAmount(): string {
  const v = SOL_MIN + Math.random() * (SOL_MAX - SOL_MIN);
  // Two decimals below 10, one decimal above — matches how a real
  // trade feed renders values (more precision when small).
  return v < 10 ? `+${v.toFixed(2)} SOL` : `+${v.toFixed(1)} SOL`;
}

// ---------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------

const Pulse: React.FC = () => {
  const [floats, setFloats] = useState<SolFloat[]>([]);
  const [missionsOpen, setMissionsOpen] = useState<boolean>(false);
  const nextId = useRef<number>(0);
  // Track scheduled timeouts so we can cancel on unmount. Without
  // this, a quick route change after a burst of taps would call
  // setState on an unmounted component → React warning.
  const timeouts = useRef<Set<ReturnType<typeof setTimeout>>>(new Set());

  const { playClick } = useClickSound();
  const tg = useTelegramWebApp();

  // Telemetry counter — purely cosmetic, drives the "TAPS" readout
  // overlay. Kept separately from the floats array so the readout
  // doesn't churn the heavy render path.
  const [tapCount, setTapCount] = useState<number>(0);

  // Sprint 19 — Pre-stamp the DeepStateIntro cooldown so a TMA user
  // who later navigates from /pulse to / does NOT face the 14s intro.
  // The intro logic in DeepStateIntro.tsx skips when
  // `deepstate.intro.lastSeenAt` is within the 24h cooldown window;
  // we set it to "now" the moment /pulse mounts, which is exactly
  // the right semantic — the user is already deep inside the brand.
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(
        "deepstate.intro.lastSeenAt",
        Date.now().toString(),
      );
    } catch {
      // Private mode / quota — silently no-op, user just sees the
      // intro on next nav. Not worth a UX prompt.
    }
  }, []);

  const handleTap = useCallback(
    (e: React.MouseEvent<HTMLDivElement> | React.TouchEvent<HTMLDivElement>): void => {
      // Resolve point — touch on mobile, pointer on desktop.
      let cx = 0;
      let cy = 0;
      if ("touches" in e && e.touches.length > 0) {
        cx = e.touches[0].clientX;
        cy = e.touches[0].clientY;
      } else if ("clientX" in e) {
        cx = e.clientX;
        cy = e.clientY;
      } else {
        return;
      }

      playClick();
      setTapCount((c) => c + 1);

      const id = ++nextId.current;
      const float: SolFloat = {
        id,
        x: cx,
        y: cy,
        amount: randomSolAmount(),
        drift: (Math.random() - 0.5) * 60,
      };
      setFloats((prev) => {
        const next = [...prev, float];
        // Trim from the front so the oldest are dropped first; this
        // preserves the "most recent" floats which are visually
        // closer to the tap and matter more.
        return next.length > MAX_CONCURRENT_FLOATS
          ? next.slice(next.length - MAX_CONCURRENT_FLOATS)
          : next;
      });

      const t = setTimeout(() => {
        setFloats((prev) => prev.filter((f) => f.id !== id));
        timeouts.current.delete(t);
      }, FLOAT_LIFETIME_MS);
      timeouts.current.add(t);
    },
    [playClick],
  );

  // Cleanup all pending timeouts on unmount.
  useEffect(() => {
    const set = timeouts.current;
    return () => {
      set.forEach((t) => clearTimeout(t));
      set.clear();
    };
  }, []);

  // Lock the document scroll while /pulse is mounted. This is an
  // arcade-mode page; allowing scroll would let the background
  // detach from the floats coordinate system.
  useEffect(() => {
    if (typeof document === "undefined") return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  // Determine if we're rendering inside Telegram — used to subtly
  // tweak the CTA label ("OPEN BOT" vs "EXECUTE ORDER" makes more
  // sense once you're already in Telegram).
  const isTma = useMemo<boolean>(() => Boolean(tg), [tg]);

  return (
    <>
      <style>{PULSE_KEYFRAMES}</style>

      <div
        className="pulse-page"
        onClick={handleTap}
        onTouchStart={handleTap}
        role="application"
        aria-label="Liquidity Pulse interactive surface"
        data-testid="pulse-page"
      >
        {/* ---------- Background image with pulse + glitch ---------- */}
        <div className="pulse-bg-wrap" aria-hidden>
          <picture>
            <source srcSet="/pulse-bg.webp" type="image/webp" />
            <img
              src="/pulse-bg.jpg"
              alt=""
              decoding="async"
              className="pulse-bg-img"
              data-testid="pulse-bg-img"
            />
          </picture>
          {/* RGB-split layers — duplicate the image with horizontal
              channel offsets via CSS filters and mix-blend-mode to
              produce a controlled glitch without WebGL. The layers
              are only visible during the glitch keyframe. */}
          <picture>
            <source srcSet="/pulse-bg.webp" type="image/webp" />
            <img
              src="/pulse-bg.jpg"
              alt=""
              decoding="async"
              className="pulse-bg-img pulse-bg-glitch-r"
              aria-hidden
            />
          </picture>
          <picture>
            <source srcSet="/pulse-bg.webp" type="image/webp" />
            <img
              src="/pulse-bg.jpg"
              alt=""
              decoding="async"
              className="pulse-bg-img pulse-bg-glitch-b"
              aria-hidden
            />
          </picture>
          {/* Vignette + scan-line texture overlay — keeps text legible
              over the busy background and reinforces the CRT vibe. */}
          <div className="pulse-vignette" />
          <div className="pulse-scanlines" />
        </div>

        {/* ---------- HUD overlay ---------- */}
        <div className="pulse-hud-top" aria-live="polite">
          <div className="pulse-hud-chip">
            <span className="pulse-hud-dot" />
            LIQUIDITY PULSE · LIVE
          </div>
          {isTma && (
            <div className="pulse-hud-chip pulse-hud-tma" data-testid="pulse-tma-chip">
              TMA MODE
            </div>
          )}
        </div>

        {/* ---------- MISSIONS button (Sprint 19) ---------- */}
        <button
          type="button"
          className="pulse-missions-btn"
          onClick={(e: React.MouseEvent<HTMLButtonElement>): void => {
            // Don't spawn a float / play click — opening the drawer
            // is a deliberate UI action, not a "pulse" tap.
            e.stopPropagation();
            setMissionsOpen(true);
          }}
          onTouchStart={(e: React.TouchEvent<HTMLButtonElement>): void => {
            e.stopPropagation();
          }}
          aria-label="Open missions drawer"
          data-testid="pulse-missions-btn"
        >
          <Shield size={14} />
          <span>MISSIONS</span>
          <span className="pulse-missions-badge" data-testid="pulse-missions-badge">
            {MISSIONS.filter((m) => m.status === "live").length}
          </span>
        </button>

        <div className="pulse-hud-counter" aria-live="polite" data-testid="pulse-tap-counter">
          <span className="pulse-hud-counter-label">TAPS</span>
          <span className="pulse-hud-counter-value">{tapCount.toLocaleString("en-US")}</span>
        </div>

        {/* ---------- Float layer ---------- */}
        <div className="pulse-floats" aria-hidden>
          {floats.map((f) => (
            <span
              key={f.id}
              className="pulse-float"
              style={{
                left: `${f.x}px`,
                top: `${f.y}px`,
                // CSS custom property drives the horizontal drift in
                // the keyframe so each float feels organic.
                ["--drift" as string]: `${f.drift}px`,
              }}
              data-testid={`pulse-float-${f.id}`}
            >
              {f.amount}
            </span>
          ))}
        </div>

        {/* ---------- Fixed CTA ---------- */}
        <div className="pulse-cta-wrap">
          <a
            href={BONKBOT_REF_URL}
            target="_blank"
            rel="noopener noreferrer"
            // Stop the tap from bubbling so the user doesn't get a
            // float + sound right under the button on the way out.
            onClick={(e: React.MouseEvent<HTMLAnchorElement>): void => {
              e.stopPropagation();
            }}
            onTouchStart={(e: React.TouchEvent<HTMLAnchorElement>): void => {
              e.stopPropagation();
            }}
            className="pulse-cta-btn"
            data-testid="pulse-cta-btn"
          >
            <Zap size={18} className="pulse-cta-icon" />
            <span className="pulse-cta-label">
              EXECUTE ORDER <span className="pulse-cta-divider">//</span> BUY $DEEP
            </span>
            <ExternalLink size={14} className="pulse-cta-external" />
          </a>
          <p className="pulse-cta-hint">
            Tap anywhere to feel the pulse · BonkBot referral · Telegram
          </p>
        </div>

        {/* ---------- MISSIONS drawer (Sprint 19) ---------- */}
        {missionsOpen && (
          <PulseMissionsDrawer onClose={(): void => setMissionsOpen(false)} />
        )}
      </div>
    </>
  );
};

export default Pulse;

// ---------------------------------------------------------------------
// Missions drawer (Sprint 19)
// ---------------------------------------------------------------------

const FAMILY_ACCENT_PULSE: Record<MissionFamily, string> = {
  infiltration: "#F59E0B",
  liquidity: "#33FF66",
  amplification: "#E11D48",
  archive: "#22D3EE",
  signal: "#A78BFA",
  classified: "#FF3B3B",
};

const FAMILY_ICON_PULSE: Record<MissionFamily, LucideIcon> = {
  infiltration: Target,
  liquidity: Wallet,
  amplification: Megaphone,
  archive: FileLock2,
  signal: Radar,
  classified: Lock,
};

interface PulseMissionsDrawerProps {
  onClose: () => void;
}

const PulseMissionsDrawer: React.FC<PulseMissionsDrawerProps> = ({ onClose }) => {
  // Close on ESC for desktop users.
  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const drawDate = useMemo(() => {
    try {
      return new Date(GIVEAWAY.drawDateIso).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      });
    } catch {
      return "May 20";
    }
  }, []);

  return (
    <div
      className="pulse-drawer-overlay"
      onClick={(e: React.MouseEvent<HTMLDivElement>): void => {
        // Click on backdrop closes; clicks on the panel are
        // stopPropagation'd below so they don't bubble.
        e.stopPropagation();
        onClose();
      }}
      onTouchStart={(e: React.TouchEvent<HTMLDivElement>): void => {
        e.stopPropagation();
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Missions panel"
      data-testid="pulse-missions-drawer"
    >
      <aside
        className="pulse-drawer-panel"
        onClick={(e: React.MouseEvent<HTMLElement>): void => {
          e.stopPropagation();
        }}
        onTouchStart={(e: React.TouchEvent<HTMLElement>): void => {
          e.stopPropagation();
        }}
      >
        <header className="pulse-drawer-header">
          <div>
            <p className="pulse-drawer-kicker">MISSIONS · CABINET ΔΣ</p>
            <h2 className="pulse-drawer-title">
              Goals · {MISSIONS.filter((m) => m.status === "live").length} active
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="pulse-drawer-close"
            aria-label="Close missions"
            data-testid="pulse-missions-drawer-close"
          >
            <XIcon size={18} />
          </button>
        </header>

        <div className="pulse-drawer-scroll">
          {/* Giveaway sticky chip at the top — most TMA traffic comes
              for the reward so we surface it first. */}
          <Link
            to="/giveaway"
            className="pulse-drawer-giveaway"
            data-testid="pulse-missions-giveaway"
          >
            <span className="pulse-drawer-giveaway-tag">★ DRAW {drawDate}</span>
            <span className="pulse-drawer-giveaway-copy">
              {GIVEAWAY.rewardSol} SOL pool · {GIVEAWAY.rules.minInvites} invites + ${GIVEAWAY.rules.minHoldingUsd} hold
            </span>
            <ArrowRight size={12} />
          </Link>

          <ul className="pulse-drawer-list" data-testid="pulse-missions-list">
            {MISSIONS.map((m) => {
              const Icon = FAMILY_ICON_PULSE[m.family];
              const accent = FAMILY_ACCENT_PULSE[m.family];
              const isRedacted = m.status === "redacted";
              return (
                <li
                  key={m.id}
                  className="pulse-drawer-item"
                  style={{
                    borderColor: isRedacted ? "rgba(255,59,59,0.35)" : accent + "55",
                  }}
                  data-testid={`pulse-mission-${m.id}`}
                >
                  <div className="pulse-drawer-item-head">
                    <span
                      className="pulse-drawer-item-icon"
                      style={{ color: accent, borderColor: accent + "66" }}
                    >
                      <Icon size={14} />
                    </span>
                    <span
                      className="pulse-drawer-item-ref"
                      style={{ color: accent }}
                    >
                      {m.dossierRef}
                    </span>
                    {isRedacted && (
                      <span className="pulse-drawer-item-redacted">CLASSIFIED</span>
                    )}
                  </div>
                  <p className={`pulse-drawer-item-title ${isRedacted ? "is-redacted" : ""}`}>
                    {/* We deliberately do NOT use i18n here — Pulse
                        drawer is operator-facing copy in EN by design
                        (the bot's UI language is English in TMA). The
                        full /missions page is i18n-driven. */}
                    {missionShortLabel(m.id)}
                  </p>
                  {!isRedacted ? (
                    <a
                      href={m.ctaUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pulse-drawer-item-cta"
                      style={{ color: accent, borderColor: accent + "60" }}
                      data-testid={`pulse-mission-cta-${m.id}`}
                    >
                      DECODE <ExternalLink size={10} />
                    </a>
                  ) : (
                    <span className="pulse-drawer-item-cta is-disabled">
                      <Lock size={10} /> SEALED
                    </span>
                  )}
                </li>
              );
            })}
          </ul>

          <Link
            to="/missions"
            className="pulse-drawer-allcta"
            data-testid="pulse-missions-see-all"
          >
            View full dossiers hub <ArrowRight size={12} />
          </Link>
        </div>
      </aside>
    </div>
  );
};

/** Pulse drawer uses condensed labels (no i18n) — keeps the TMA UI
 *  tight on tiny mobile heights where a 12-word card title would
 *  blow up the layout. The /missions page renders full bilingual
 *  copy. */
function missionShortLabel(id: string): string {
  switch (id) {
    case "infiltration": return "OPERATION: INFILTRATION — 3 invites";
    case "liquidity":    return "PROTOCOL: LIQUIDITY — Hold $30 of $DEEP";
    case "amplification": return "DIRECTIVE: AMPLIFICATION — 3 retweets";
    case "archive":      return "ARCHIVE: WHITELIST — Submit handle";
    case "signal":       return "SIGNAL: AUTHORITY — Join + verify";
    case "future_06":    return "OPERATION ████████";
    default:             return id.toUpperCase();
  }
}

// ---------------------------------------------------------------------
// CSS — co-located. Inlined via <style> so we don't need a
// component-scoped stylesheet pipeline. All animations are restricted
// to transform + opacity for compositor-only repaint cost.
// ---------------------------------------------------------------------
const PULSE_KEYFRAMES = `
.pulse-page {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  /* Telegram WebApp viewport variable — falls back to 100vh outside TMA. */
  height: var(--tg-viewport-stable-height, 100vh);
  background: #000;
  color: #d8ffe6;
  font-family: 'Source Code Pro', 'Roboto Mono', ui-monospace, monospace;
  overflow: hidden;
  touch-action: manipulation; /* removes the 300ms iOS click delay */
  user-select: none;
  -webkit-user-select: none;
  cursor: crosshair;
  isolation: isolate;
  z-index: 0;
}

.pulse-bg-wrap {
  position: absolute;
  inset: 0;
  overflow: hidden;
}
.pulse-bg-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 28%;
  will-change: transform, opacity, filter;
  animation: pulse-breathe 4.2s ease-in-out infinite,
             pulse-glitch-base 8s linear infinite;
}
.pulse-bg-glitch-r,
.pulse-bg-glitch-b {
  mix-blend-mode: screen;
  opacity: 0;
  pointer-events: none;
}
.pulse-bg-glitch-r {
  filter: drop-shadow(0 0 0 rgba(0,0,0,0)) hue-rotate(-15deg) saturate(1.6);
  animation: pulse-glitch-r 8s steps(1, end) infinite;
}
.pulse-bg-glitch-b {
  filter: hue-rotate(150deg) saturate(2);
  animation: pulse-glitch-b 8s steps(1, end) infinite;
}

/* Subtle "breathing" scale — never exceeds 1.04 to avoid noticeable
   reflow of the visible composition. */
@keyframes pulse-breathe {
  0%, 100% { transform: scale(1.0); filter: brightness(0.95) contrast(1.05); }
  50%      { transform: scale(1.035); filter: brightness(1.08) contrast(1.15); }
}

/* The "always on" minor flicker — runs in parallel with breathe. */
@keyframes pulse-glitch-base {
  0%, 92%, 100% { opacity: 1; transform: translate3d(0,0,0) scale(1); }
  93%           { opacity: 0.88; transform: translate3d(-2px, 0, 0) scale(1.002); }
  94%           { opacity: 1;    transform: translate3d(3px, 0, 0) scale(1); }
  95%           { opacity: 0.7;  transform: translate3d(0, 1px, 0) scale(1.001); }
  96%           { opacity: 1; }
}

/* Red channel: only visible during a brief 1-frame slice every 8s */
@keyframes pulse-glitch-r {
  0%, 92%, 100% { opacity: 0; transform: translate3d(0,0,0); }
  93%, 95%      { opacity: 0.55; transform: translate3d(-6px, 0, 0); }
  94%           { opacity: 0; }
}
/* Blue channel: complementary slice, opposite direction */
@keyframes pulse-glitch-b {
  0%, 92%, 100% { opacity: 0; transform: translate3d(0,0,0); }
  93%, 95%      { opacity: 0.5; transform: translate3d(6px, 0, 0); }
  94%           { opacity: 0; }
}

.pulse-vignette {
  position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(ellipse at center, rgba(0,0,0,0) 40%, rgba(0,0,0,0.55) 75%, rgba(0,0,0,0.9) 100%),
    linear-gradient(to bottom, rgba(0,0,0,0) 60%, rgba(0,0,0,0.6) 100%);
}
.pulse-scanlines {
  position: absolute; inset: 0; pointer-events: none;
  background-image: repeating-linear-gradient(
    to bottom,
    rgba(0,0,0,0) 0,
    rgba(0,0,0,0) 2px,
    rgba(0,0,0,0.18) 3px,
    rgba(0,0,0,0) 4px
  );
  mix-blend-mode: multiply;
  opacity: 0.5;
}

/* ---------- HUD ---------- */
.pulse-hud-top {
  position: absolute;
  top: env(safe-area-inset-top, 16px);
  left: 16px;
  right: 16px;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
  z-index: 10;
}
.pulse-hud-chip {
  font-size: 10px;
  letter-spacing: 0.2em;
  padding: 6px 10px;
  border-radius: 2px;
  background: rgba(0, 12, 6, 0.6);
  border: 1px solid rgba(51, 255, 51, 0.45);
  color: #6effa1;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.pulse-hud-tma {
  border-color: rgba(34, 211, 238, 0.45);
  color: #67e8f9;
}
.pulse-hud-dot {
  width: 6px; height: 6px;
  border-radius: 999px;
  background: #33ff33;
  box-shadow: 0 0 8px #33ff33;
  animation: pulse-dot 1.4s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.4; transform: scale(0.7); }
}
.pulse-hud-counter {
  position: absolute;
  top: calc(env(safe-area-inset-top, 16px) + 44px);
  right: 16px;
  pointer-events: none;
  background: rgba(0, 12, 6, 0.55);
  border: 1px solid rgba(51, 255, 51, 0.3);
  border-radius: 2px;
  padding: 6px 10px;
  text-align: right;
  z-index: 10;
}
.pulse-hud-counter-label {
  display: block;
  font-size: 9px;
  letter-spacing: 0.25em;
  color: rgba(110, 255, 161, 0.65);
}
.pulse-hud-counter-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #d6ffe2;
  text-shadow: 0 0 10px rgba(51, 255, 51, 0.4);
}

/* ---------- Floats ---------- */
.pulse-floats {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 5;
}
.pulse-float {
  position: absolute;
  transform: translate(-50%, -50%);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #33ff66;
  text-shadow:
    0 0 6px rgba(51, 255, 102, 0.95),
    0 0 14px rgba(51, 255, 102, 0.7),
    0 0 28px rgba(51, 255, 102, 0.35);
  /* Sharp digital readout effect via dual-shadow stroke */
  -webkit-text-stroke: 0.4px rgba(0, 32, 12, 0.5);
  white-space: nowrap;
  animation: pulse-float-up 1s ease-out forwards;
  will-change: transform, opacity;
}
@keyframes pulse-float-up {
  0%   { transform: translate(-50%, -50%) scale(0.6); opacity: 0; }
  12%  { transform: translate(calc(-50% + (var(--drift, 0px) * 0.25)), calc(-50% - 12px)) scale(1.05); opacity: 1; }
  60%  { transform: translate(calc(-50% + (var(--drift, 0px) * 0.7)), calc(-50% - 60px)) scale(1); opacity: 1; }
  100% { transform: translate(calc(-50% + var(--drift, 0px)), calc(-50% - 110px)) scale(0.95); opacity: 0; }
}

/* ---------- CTA ---------- */
.pulse-cta-wrap {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(env(safe-area-inset-bottom, 12px) + 16px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: min(420px, calc(100vw - 32px));
  z-index: 15;
}
.pulse-cta-btn {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 22px;
  background: linear-gradient(135deg, #0a3a18 0%, #128a3a 50%, #18c964 100%);
  color: #f0fff5;
  text-decoration: none;
  font-weight: 700;
  letter-spacing: 0.12em;
  font-size: 15px;
  border-radius: 4px;
  border: 1px solid rgba(110, 255, 161, 0.6);
  box-shadow:
    0 0 24px rgba(51, 255, 102, 0.45),
    inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  position: relative;
  overflow: hidden;
  transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease;
}
.pulse-cta-btn::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.18) 50%, transparent 100%);
  transform: translateX(-100%);
  animation: pulse-cta-shine 3.2s ease-in-out infinite;
}
@keyframes pulse-cta-shine {
  0%, 70%, 100% { transform: translateX(-100%); }
  85% { transform: translateX(100%); }
}
.pulse-cta-btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.05);
  box-shadow:
    0 0 36px rgba(51, 255, 102, 0.65),
    inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}
.pulse-cta-btn:active {
  transform: translateY(1px);
  filter: brightness(0.95);
}
.pulse-cta-btn:focus-visible {
  outline: 2px solid #33ff66;
  outline-offset: 3px;
}
.pulse-cta-icon { color: #d8ffe6; }
.pulse-cta-external { color: rgba(216, 255, 230, 0.7); }
.pulse-cta-divider { opacity: 0.55; margin: 0 4px; }
.pulse-cta-hint {
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(216, 255, 230, 0.55);
  text-align: center;
  text-shadow: 0 1px 4px rgba(0,0,0,0.7);
}

/* Reduced motion accommodation — strips the heavy animations for
   users who opted out via OS preferences. The CTA and floats still
   work; only the background "alive" effects are stilled. */
@media (prefers-reduced-motion: reduce) {
  .pulse-bg-img,
  .pulse-bg-glitch-r,
  .pulse-bg-glitch-b,
  .pulse-cta-btn::before {
    animation: none !important;
  }
}

/* ---------- MISSIONS button + drawer (Sprint 19) ---------- */
.pulse-missions-btn {
  position: absolute;
  /* Place it below the LIVE chip on the left so it stacks with the
     TAPS counter on the right — both peripheral, neither obstructing
     the central artwork. */
  top: calc(env(safe-area-inset-top, 16px) + 44px);
  left: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 11px 7px 9px;
  border-radius: 4px;
  background: linear-gradient(135deg, rgba(225,29,72,0.18) 0%, rgba(245,158,11,0.16) 100%);
  border: 1px solid rgba(255, 59, 59, 0.55);
  color: #FFB68C;
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.18em;
  cursor: pointer;
  z-index: 11;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  box-shadow: 0 0 18px -6px rgba(225, 29, 72, 0.65);
  transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
}
.pulse-missions-btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.08);
  box-shadow: 0 0 24px -4px rgba(225, 29, 72, 0.85);
}
.pulse-missions-btn:active { transform: translateY(1px); }
.pulse-missions-btn:focus-visible { outline: 2px solid #F59E0B; outline-offset: 3px; }
.pulse-missions-badge {
  display: inline-grid;
  place-items: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #F59E0B;
  color: #1A0E03;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

/* Drawer overlay + panel */
.pulse-drawer-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 30;
  display: flex;
  justify-content: flex-end;
  animation: pulse-drawer-fade 220ms ease-out both;
}
@keyframes pulse-drawer-fade {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.pulse-drawer-panel {
  width: min(420px, 100vw);
  height: 100%;
  background: linear-gradient(180deg, rgba(8, 4, 4, 0.98) 0%, rgba(15, 8, 8, 0.98) 100%);
  border-left: 1px solid rgba(255, 59, 59, 0.45);
  box-shadow: -24px 0 60px -20px rgba(225, 29, 72, 0.45);
  display: flex;
  flex-direction: column;
  animation: pulse-drawer-slide 260ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
@keyframes pulse-drawer-slide {
  from { transform: translateX(20px); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}
.pulse-drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 18px 14px;
  border-bottom: 1px solid rgba(255, 59, 59, 0.18);
}
.pulse-drawer-kicker {
  font-size: 9px;
  letter-spacing: 0.28em;
  color: #FF6B6B;
  margin: 0;
}
.pulse-drawer-title {
  margin: 4px 0 0;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #FFE4D4;
}
.pulse-drawer-close {
  background: transparent;
  border: 1px solid rgba(255, 59, 59, 0.35);
  border-radius: 4px;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  color: #FFB68C;
  cursor: pointer;
  transition: background 160ms ease;
}
.pulse-drawer-close:hover { background: rgba(255, 59, 59, 0.12); }
.pulse-drawer-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px 16px 24px;
}
.pulse-drawer-giveaway {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 14px;
  border-radius: 4px;
  border: 1px solid rgba(245, 158, 11, 0.5);
  background: linear-gradient(135deg, rgba(245,158,11,0.14) 0%, rgba(225,29,72,0.08) 100%);
  color: #FFD7A0;
  text-decoration: none;
  font-size: 11px;
  letter-spacing: 0.12em;
  transition: background 160ms ease, transform 160ms ease;
}
.pulse-drawer-giveaway:hover {
  background: linear-gradient(135deg, rgba(245,158,11,0.22) 0%, rgba(225,29,72,0.12) 100%);
  transform: translateY(-1px);
}
.pulse-drawer-giveaway-tag {
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #FFB94A;
  white-space: nowrap;
}
.pulse-drawer-giveaway-copy {
  flex: 1;
  font-size: 10px;
  color: rgba(255, 215, 160, 0.85);
  letter-spacing: 0.06em;
}
.pulse-drawer-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pulse-drawer-item {
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  padding: 12px 14px;
  background: rgba(20, 10, 10, 0.6);
}
.pulse-drawer-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.pulse-drawer-item-icon {
  width: 22px; height: 22px;
  display: grid; place-items: center;
  border: 1px solid;
  border-radius: 3px;
  background: rgba(0,0,0,0.4);
}
.pulse-drawer-item-ref {
  font-size: 9px;
  letter-spacing: 0.22em;
  font-weight: 600;
}
.pulse-drawer-item-redacted {
  margin-left: auto;
  font-size: 8px;
  letter-spacing: 0.22em;
  padding: 2px 6px;
  border: 1px solid rgba(255,59,59,0.5);
  color: #FF6B6B;
  border-radius: 2px;
}
.pulse-drawer-item-title {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #FFE4D4;
  line-height: 1.4;
}
.pulse-drawer-item-title.is-redacted {
  color: rgba(255, 107, 107, 0.55);
  font-style: italic;
}
.pulse-drawer-item-cta {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  border: 1px solid;
  border-radius: 3px;
  font-size: 10px;
  letter-spacing: 0.22em;
  font-weight: 700;
  text-decoration: none;
  background: rgba(0,0,0,0.3);
  transition: background 160ms ease;
}
.pulse-drawer-item-cta:hover { background: rgba(255,255,255,0.04); }
.pulse-drawer-item-cta.is-disabled {
  color: rgba(255, 107, 107, 0.6);
  border-color: rgba(255, 59, 59, 0.35);
  cursor: not-allowed;
}
.pulse-drawer-allcta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  padding: 10px 14px;
  background: #F59E0B;
  color: #1A0E03;
  border-radius: 4px;
  text-decoration: none;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  width: 100%;
  justify-content: center;
  transition: background 160ms ease;
}
.pulse-drawer-allcta:hover { background: #FFB94A; }
`;
