/**
 * Centralised framer-motion variants & transitions.
 *
 * Why this file exists
 * --------------------
 * Inline objects in motion props (`initial={{ opacity: 0 }}`,
 * `transition={{ duration: 0.4 }}` etc.) are recreated on every render.
 * That breaks framer-motion's identity-based memoisation and forces
 * tween restarts on parent re-renders — most visible as flickering
 * fade-ins or stuttery scroll-triggered animations.
 *
 * By exporting these objects at module scope, every consumer reuses
 * the SAME reference across all renders: framer-motion sees the
 * identity is stable and skips redundant work.
 *
 * Naming convention
 * -----------------
 * - SCREAMING_SNAKE_CASE so they look like constants in the call site.
 * - Suffix conveys role:
 *     `_INITIAL`     — initial state
 *     `_ANIMATE`     — animate state
 *     `_EXIT`        — exit state (AnimatePresence)
 *     `_TRANSITION`  — transition options
 *     `_VIEWPORT`    — viewport options for `whileInView`
 *
 * - Composite variants (Variants object) get a single name (e.g.
 *   `FADE_UP_VARIANTS`) — use with `<motion.div variants={...} />`.
 *
 * Add new variants here when you find yourself duplicating the same
 * inline object twice or more.
 */

import type { Variants, Transition } from "framer-motion";

// =========================================================================
// Viewport options (whileInView)
// =========================================================================

/** Trigger once, 80px before the element enters the viewport. */
export const VIEWPORT_ONCE_M80 = { once: true, margin: "-80px" } as const;

/** Trigger once, 60px before the element enters the viewport. */
export const VIEWPORT_ONCE_M60 = { once: true, margin: "-60px" } as const;

/** Trigger once, immediately on enter. */
export const VIEWPORT_ONCE = { once: true } as const;

// =========================================================================
// FADE
// =========================================================================

export const FADE_INITIAL = { opacity: 0 };
export const FADE_ANIMATE = { opacity: 1 };
export const FADE_EXIT = { opacity: 0 };

export const FADE_TRANSITION_FAST: Transition = { duration: 0.25 };
export const FADE_TRANSITION_DEFAULT: Transition = { duration: 0.5 };
export const FADE_TRANSITION_SLOW: Transition = { duration: 0.8 };

// =========================================================================
// FADE-UP (slide up + fade in) — workhorse for section reveal
// =========================================================================

/** y=12 starting offset — light feel, default for headers and cards. */
export const FADE_UP_12_INITIAL = { opacity: 0, y: 12 };
/** y=14 starting offset — slightly heavier, for hero sub-blocks. */
export const FADE_UP_14_INITIAL = { opacity: 0, y: 14 };
/** y=10 starting offset — minimal, for inline alerts / CTA reveals. */
export const FADE_UP_10_INITIAL = { opacity: 0, y: 10 };

export const FADE_UP_ANIMATE = { opacity: 1, y: 0 };

/** Standard scroll-into-view transition. */
export const FADE_UP_TRANSITION: Transition = { duration: 0.5 };
/** Slightly slower for first-paint hero elements. */
export const FADE_UP_TRANSITION_SLOW: Transition = { duration: 0.6, delay: 0.05 };
/** Staggered for "second" elements in a row (small offset). */
export const FADE_UP_TRANSITION_STAGGER_1: Transition = {
  duration: 0.5,
  delay: 0.08,
};
/** Staggered for "second" elements with a larger offset. */
export const FADE_UP_TRANSITION_STAGGER_2: Transition = {
  duration: 0.5,
  delay: 0.1,
};
/** Hero entry — a touch slower, slight delay so it lands after page paint. */
export const FADE_UP_TRANSITION_HERO: Transition = {
  duration: 0.6,
  delay: 0.1,
};
/** Used for ROI simulator-class cards. */
export const FADE_UP_TRANSITION_ROI: Transition = { duration: 0.55 };

/** Composite variants for `<motion.div variants={...}>` usage. */
export const FADE_UP_VARIANTS: Variants = {
  initial: FADE_UP_12_INITIAL,
  animate: FADE_UP_ANIMATE,
  exit: { opacity: 0, y: 12 },
};

// =========================================================================
// FADE-UP-SCALE (used for declassified CTAs and similar "wow" reveals)
// =========================================================================

export const FADE_UP_SCALE_INITIAL = { opacity: 0, y: 12, scale: 0.98 };
export const FADE_UP_SCALE_ANIMATE = { opacity: 1, y: 0, scale: 1 };
export const FADE_UP_SCALE_EXIT = { opacity: 0 };

// =========================================================================
// PULSE / BREATHING (looping ambient animations)
// =========================================================================

/** Soft breathing opacity loop for ambient halos. */
export const HALO_PULSE_ANIMATE = { opacity: [0.4, 0.9, 0.4] };
export const HALO_PULSE_TRANSITION: Transition = {
  duration: 2.2,
  repeat: Infinity,
};

/** Heavier breathing — for door-keypad ambient glow. */
export const KEYPAD_PULSE_ANIMATE = { opacity: [0.45, 0.9, 0.45] };
export const KEYPAD_PULSE_TRANSITION: Transition = {
  duration: 2.4,
  repeat: Infinity,
  ease: "easeInOut",
};

/** Ultra-soft breathing — for verify-state warning flash. */
export const VERIFY_FLASH_ANIMATE = { opacity: [0.0, 0.18, 0.0] };
export const VERIFY_FLASH_TRANSITION: Transition = {
  duration: 1.6,
  repeat: Infinity,
};

/** Subtle scale breathing — for primary CTA buttons that need attention. */
export const CTA_BREATHE_INITIAL = { scale: 1 };
export const CTA_BREATHE_ANIMATE = { scale: [1, 1.04, 1] };
export const CTA_BREATHE_TRANSITION: Transition = {
  duration: 1.8,
  repeat: Infinity,
};
