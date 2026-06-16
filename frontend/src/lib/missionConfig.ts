/**
 * lib/missionConfig.ts — Sprint 21 typed client for the Mission Command
 * Center backend.
 *
 * Centralises all API calls so components stay declarative. Pure
 * types + thin axios wrappers.
 */
import axios, { AxiosInstance } from "axios";

const BACKEND_URL: string = process.env.REACT_APP_BACKEND_URL || "";
export const API_BASE: string = `${BACKEND_URL}/api`;

export const missionApi: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 15_000,
  headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------
// Types (mirror routers/missions_command.py response models)
// ---------------------------------------------------------------------
export type MissionStatus = "live" | "redacted" | "completed";
export type MissionId =
  | "infiltration"
  | "liquidity"
  | "amplification"
  | "archive"
  | "signal"
  | "future_06";

export interface PerMissionOverride {
  status: MissionStatus;
  cta_url: string | null;
  label_date_iso: string | null;
}

export interface MissionConfig {
  giveaway_draw_date_iso: string;
  giveaway_snapshot_date_iso: string;
  giveaway_reward_sol: number;
  giveaway_winners_count: number;
  giveaway_min_invites: number;
  giveaway_min_holding_usd: number;
  extraction_chamber_title_fr: string | null;
  extraction_chamber_title_en: string | null;
  extraction_chamber_subtitle_fr: string | null;
  extraction_chamber_subtitle_en: string | null;
  extraction_chamber_body_fr: string | null;
  extraction_chamber_body_en: string | null;
  missions: Record<string, PerMissionOverride>;
  emails_enabled: boolean;
  emails_helius_auto_send: boolean;
  emails_sender_name: string;
  updated_at: string | null;
  updated_by: string | null;
}

export interface IllustrationStatus {
  present: boolean;
  size_bytes: number;
  public_path: string;
}

export interface AdminSnapshot {
  config: MissionConfig;
  participation_counts: Record<string, number>;
  illustrations: Record<string, IllustrationStatus>;
}

export interface Participation {
  _id: string;
  mission_id: string;
  email: string;
  wallet_address: string | null;
  locale: string;
  source: string;
  email_sent: boolean;
  email_sent_at: string | null;
  email_message_id: string | null;
  email_last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ParticipationSubmitPayload {
  mission_id: string;
  email: string;
  wallet_address?: string;
  locale: "fr" | "en";
}

export interface ParticipationAck {
  ok: boolean;
  participation_id: string;
  email_queued: boolean;
}

// ---------------------------------------------------------------------
// Public endpoints (no auth)
// ---------------------------------------------------------------------
export async function fetchMissionConfig(): Promise<MissionConfig> {
  const res = await missionApi.get<MissionConfig>("/mission-config");
  return res.data;
}

export async function submitMissionParticipation(
  payload: ParticipationSubmitPayload
): Promise<ParticipationAck> {
  const res = await missionApi.post<ParticipationAck>(
    "/mission-participations",
    payload
  );
  return res.data;
}

// ---------------------------------------------------------------------
// Admin endpoints (JWT required — caller must set Authorization header)
// ---------------------------------------------------------------------
function authConfig(token: string): { headers: { Authorization: string } } {
  return { headers: { Authorization: `Bearer ${token}` } };
}

export async function adminGetSnapshot(token: string): Promise<AdminSnapshot> {
  const res = await missionApi.get<AdminSnapshot>(
    "/admin/mission-config/snapshot",
    authConfig(token)
  );
  return res.data;
}

export async function adminUpdateConfig(
  token: string,
  patch: Partial<MissionConfig>
): Promise<{ ok: boolean; config: MissionConfig }> {
  const res = await missionApi.put<{ ok: boolean; config: MissionConfig }>(
    "/admin/mission-config",
    patch,
    authConfig(token)
  );
  return res.data;
}

export async function adminRegenerateIllustration(
  token: string,
  missionId: string
): Promise<{ ok: boolean; size_bytes: number; public_path: string }> {
  const res = await missionApi.post<{
    ok: boolean;
    size_bytes: number;
    public_path: string;
  }>(
    `/admin/mission-config/illustrations/${encodeURIComponent(missionId)}/regenerate`,
    {},
    { ...authConfig(token), timeout: 90_000 }
  );
  return res.data;
}

export async function adminListParticipations(
  token: string,
  missionId?: string
): Promise<{ participations: Participation[]; count: number }> {
  const url =
    "/admin/mission-participations" +
    (missionId ? `?mission_id=${encodeURIComponent(missionId)}` : "");
  const res = await missionApi.get<{
    participations: Participation[];
    count: number;
  }>(url, authConfig(token));
  return res.data;
}

export async function adminResendParticipationEmail(
  token: string,
  participationId: string
): Promise<{ ok: boolean }> {
  const res = await missionApi.post<{ ok: boolean }>(
    `/admin/mission-participations/${encodeURIComponent(participationId)}/resend`,
    {},
    authConfig(token)
  );
  return res.data;
}

// ---------------------------------------------------------------------
// Formatting helpers (used by both public & admin pages)
// ---------------------------------------------------------------------
export function formatGiveawayDate(
  iso: string,
  locale: "fr" | "en" = "fr"
): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat(locale === "fr" ? "fr-FR" : "en-US", {
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(d);
  } catch {
    return iso;
  }
}

export function formatGiveawayDateShort(
  iso: string,
  locale: "fr" | "en" = "fr"
): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat(locale === "fr" ? "fr-FR" : "en-US", {
      day: "numeric",
      month: "long",
    }).format(d);
  } catch {
    return iso;
  }
}
