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

// ---- Public stats ---------------------------------------------------------
export interface PublicStats {
  whitelist_count: number;
  chat_messages: number;
  prophecies_served: number;
  vault?: VaultState;
}

// ---- i18n -----------------------------------------------------------------
export type Lang = "fr" | "en";
