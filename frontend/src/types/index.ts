/**
 * Shared TypeScript type definitions for $DEEPOTUS.
 *
 * These mirror the public Pydantic models exposed by the FastAPI backend.
 * Keep them in sync when adjusting backend response shapes.
 */

// ---- Vault state (public + classified-vault polling) ----------------------
export type VaultStage =
  | "LOCKED"
  | "UNLOCKING"
  | "CRACKING"
  | "DECLASSIFIED";

export type DexMode = "off" | "demo" | "live";

export interface VaultEvent {
  id: string;
  ts: string; // ISO date
  kind: string; // "buy" | "sell" | "tick" | ...
  amount?: number;
  message?: string;
}

export interface VaultState {
  stage: VaultStage;
  digits_locked: number;
  current_combination: number[];
  target_combination: number[];
  tokens_sold: number;
  progress_pct: number;
  treasury_eur_value: number;
  treasury_progress_pct: number;
  micro_ticks_total: number;
  dex_mode: DexMode;
  dex_label: string | null;
  recent_events: VaultEvent[];
}

// ---- Access card / classified-vault session -------------------------------
export interface AccessSession {
  ok: boolean;
  session_token: string;
  accreditation_number: string;
  display_name: string;
  issued_at: string;
  expires_at: string;
}

// ---- Bot config / Prophet Studio ------------------------------------------
export type BotPlatform = "x" | "telegram";
export type ContentType =
  | "alpha_drop"
  | "macro_take"
  | "kol_reply"
  | "wisdom"
  | "satire";

export interface BotPostPreview {
  content_type: ContentType;
  platform: BotPlatform;
  char_budget: number;
  provider: string;
  model: string;
  content_fr: string;
  content_en: string;
  hashtags: string[];
  primary_emoji: string;
}

export interface BotConfig {
  kill_switch_active: boolean;
  default_provider: string;
  default_model: string;
  cron_minutes: number;
  enabled_platforms: BotPlatform[];
  enabled_types: ContentType[];
}

// ---- Loyalty engine (Sprints 3 + 4) ---------------------------------------
export interface LoyaltyTier {
  tier: string;
  lower_pct: number;
  upper_pct: number;
  hints_fr: string[];
  hints_en: string[];
}

export interface LoyaltyStatus {
  hints_enabled: boolean;
  email_enabled: boolean;
  email_delay_hours: number;
  progress_percent: number;
  current_tier: string;
  sample_hint_fr: string | null;
  sample_hint_en: string | null;
  tiers: LoyaltyTier[];
}

export interface LoyaltyEmailStats {
  total_sent: number;
  last_sent_at: string | null;
  last_recipient: string | null;
  pending_now: number;
}

export interface LoyaltyTestSendResult {
  status: string;
  email: string;
  accred?: string | null;
  lang?: string | null;
  email_id?: string | null;
  error?: string | null;
  prophet_message?: string | null;
}

// ---- News repost (auto-relay top RSS headlines) ---------------------------
export interface NewsRepostQueueItem {
  title: string;
  source: string | null;
  url: string;
  preview_text: string;
}

export interface NewsRepostConfig {
  enabled_for: { x: boolean; telegram: boolean };
  interval_minutes: number;
  delay_after_refresh_minutes: number;
  wait_after_prophet_post_minutes: number;
  daily_cap: number;
  prefix_fr: string;
  prefix_en: string;
}

export interface NewsRepostStatus {
  config: NewsRepostConfig;
  credentials_present: { x: boolean; telegram: boolean };
  today_per_platform: { x: number; telegram: number };
  last_per_platform: { x: string | null; telegram: string | null };
  queue_preview: { x: NewsRepostQueueItem[]; telegram: NewsRepostQueueItem[] };
}

export interface NewsRepostTestResult {
  status: string;
  platform: string;
  post_id?: string | null;
  preview_text?: string | null;
  title?: string | null;
  link?: string | null;
  error?: string | null;
  hint?: string | null;
}


// ---- Public stats ---------------------------------------------------------
export interface PublicStats {
  whitelist_count: number;
  chat_messages: number;
  prophecies_served: number;
  vault?: VaultState;
}

// ---- i18n -----------------------------------------------------------------
export type Lang = "fr" | "en";
