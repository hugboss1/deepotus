/**
 * lib/missions.ts — Static data layer for Sprint 19 Missions Hub & Giveaway.
 *
 * Why a static module (not a backend collection)?
 *  - At launch we only have ~6 missions, all editorially curated. A
 *    DB would add operational weight (admin UI, migrations,
 *    redactions) for zero current benefit.
 *  - Mission copy is bilingual and tightly choreographed with the
 *    rest of the site's i18n; keeping them as keys in
 *    `translations.js` rather than a DB makes proofreading trivial.
 *  - When mission count grows past ~20 OR we need per-user
 *    tracking, migrate to `mission_logs` Mongo collection (see
 *    burn_logs.py for the pattern).
 *
 * The module exports:
 *  - {@link MISSIONS} — ordered list rendered on /missions and the
 *    landing preview. Order matters (top → bottom = priority).
 *  - {@link FEATURED_MISSION_KEYS} — subset shown on the landing
 *    preview teaser (max 3 by design to leave a "see more" pull).
 *  - {@link GIVEAWAY} — single source of truth for the May 20 draw
 *    rules so /giveaway, /missions, and Pulse all stay in lockstep.
 *
 * All copy ties back to i18n via `i18nKey` — never hardcode mission
 * strings in components. Tests should never assert on label English;
 * assert on `data-testid` or the i18n key path.
 */

/**
 * Public Telegram channel — canonical. If we ever rename the bot or
 * channel, update this single constant and every "DECODE MISSION"
 * link follows automatically.
 */
export const TELEGRAM_CHANNEL_URL = "https://t.me/deepotus";

/** Bonkbot referral entrypoint, mirrored from Pulse.tsx so Missions
 * Hub can route directly into the buy flow without round-tripping. */
export const BONKBOT_REF_URL = "https://t.me/bonkbot_bot?start=ref_osca5";

export type MissionStatus = "live" | "redacted" | "completed";
export type MissionFamily = "infiltration" | "liquidity" | "amplification" | "archive" | "signal" | "classified";

export interface Mission {
  /** Stable id — used in data-testid and i18n key path. */
  id: string;
  /** Family drives the accent color + icon mapping. */
  family: MissionFamily;
  /** Cabinet-grade dossier ref shown as a chip top-left of each card. */
  dossierRef: string;
  /** i18n key root under `missionsPage.cards.{id}.{title|brief|reward|action}`. */
  i18nKey: string;
  /** "live" → fully revealed + DECODE button.
   *  "redacted" → blurred title, no action, anticipation builder.
   *  "completed" → grey card with checkmark (for future). */
  status: MissionStatus;
  /** Where DECODE MISSION sends the user. Always external/Telegram.
   *  Redacted missions ignore this. */
  ctaUrl: string;
  /** Optional secondary action key (used on a few missions only). */
  secondaryCtaUrl?: string;
}

/**
 * Ordered mission roster. Order is significant — top-of-list ranks
 * higher in the preview teaser on the landing.
 */
export const MISSIONS: Mission[] = [
  {
    id: "infiltration",
    family: "infiltration",
    dossierRef: "OPERATION · 001",
    i18nKey: "infiltration",
    status: "live",
    ctaUrl: TELEGRAM_CHANNEL_URL,
  },
  {
    id: "liquidity",
    family: "liquidity",
    dossierRef: "PROTOCOL · 002",
    i18nKey: "liquidity",
    status: "live",
    ctaUrl: TELEGRAM_CHANNEL_URL,
    secondaryCtaUrl: BONKBOT_REF_URL,
  },
  {
    id: "amplification",
    family: "amplification",
    dossierRef: "DIRECTIVE · 003",
    i18nKey: "amplification",
    status: "live",
    ctaUrl: TELEGRAM_CHANNEL_URL,
  },
  {
    id: "archive",
    family: "archive",
    dossierRef: "ARCHIVE · 004",
    i18nKey: "archive",
    status: "live",
    ctaUrl: TELEGRAM_CHANNEL_URL,
  },
  {
    id: "signal",
    family: "signal",
    dossierRef: "SIGNAL · 005",
    i18nKey: "signal",
    status: "live",
    ctaUrl: TELEGRAM_CHANNEL_URL,
  },
  {
    id: "future_06",
    family: "classified",
    dossierRef: "OPERATION · 006",
    i18nKey: "future_06",
    status: "redacted",
    ctaUrl: TELEGRAM_CHANNEL_URL,
  },
];

/** Featured = top 3 missions surfaced on the Landing teaser. */
export const FEATURED_MISSION_KEYS: readonly string[] = [
  "infiltration",
  "liquidity",
  "amplification",
] as const;

// ---------------------------------------------------------------------
// Giveaway (Sprint 19)
// ---------------------------------------------------------------------

/**
 * Single source of truth for the May 20 community draw.
 *
 * Important: the date is stored as a UTC midnight ISO so the
 * countdown rendered on /giveaway shows the same "time left" to
 * everyone regardless of their browser timezone. Localising the
 * displayed date is done in the page component via `toLocaleString`.
 */
export const GIVEAWAY = {
  /** UTC ISO of the draw moment (May 20, 2026 — 18:00 UTC). */
  drawDateIso: "2026-05-20T18:00:00Z",
  /** Reward pool — single source of truth. */
  rewardSol: 5,
  /** Eligibility — both rules MUST be satisfied. */
  rules: {
    minInvites: 3,
    minHoldingUsd: 30,
  },
} as const;
