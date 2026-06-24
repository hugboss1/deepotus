/**
 * AdminMissionsCommand.tsx — Sprint 21 Command Center for the council
 * missions.
 *
 * One page, four sections:
 *   1. Giveaway parameters
 *      (draw date, snapshot date, reward SOL, winners, min invites,
 *       min holding USD)
 *   2. Extraction Chamber overrides (FR + EN strings, null = use i18n)
 *   3. Per-mission overrides (status live/redacted/completed, CTA URL,
 *      label_date for the card UI)
 *   4. Email automation & AI illustrations
 *      (toggle emails on/off, regenerate each mission's gpt-image-1
 *       illustration, list last 50 participations with resend button)
 *
 * Auth: JWT via ``getAdminToken``. Redirects to ``/admin`` if absent.
 *
 * UX rules (per design guidelines):
 *  - All inputs are Shadcn (Input, Switch, Select, Textarea).
 *  - Save buttons are explicit per section to avoid accidental writes.
 *  - Optimistic local state, server PUT, then refetch snapshot.
 *  - Toast on success / error.
 *  - data-testid on every actionable element.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCcw,
  Send,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Mail,
  Image as ImageIcon,
  Settings,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getAdminToken } from "@/lib/adminAuth";
import {
  adminGetSnapshot,
  adminListParticipations,
  adminResendParticipationEmail,
  adminUpdateConfig,
  type AdminSnapshot,
  type MissionConfig,
  type Participation,
  type PerMissionOverride,
} from "@/lib/missionConfig";

const KNOWN_MISSION_IDS: ReadonlyArray<string> = [
  "infiltration",
  "liquidity",
  "amplification",
  "archive",
  "signal",
  "future_06",
];

// Convert an ISO-Z string to ``"YYYY-MM-DDTHH:mm"`` (the format accepted
// by <input type="datetime-local">). Returns "" for invalid input so the
// input stays empty rather than rendering "Invalid Date".
function isoToInput(iso: string): string {
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "";
    // Output UTC slice (we never edit timezone — server stores UTC).
    return d.toISOString().slice(0, 16);
  } catch {
    return "";
  }
}

function inputToIso(local: string): string {
  if (!local) return "";
  try {
    // Treat the input value as UTC since we explicitly serve UTC.
    const d = new Date(local + ":00Z");
    return d.toISOString();
  } catch {
    return local;
  }
}

export default function AdminMissionsCommand(): JSX.Element {
  const navigate = useNavigate();
  const [token] = useState<string | null>(() => getAdminToken() || null);

  const [snapshot, setSnapshot] = useState<AdminSnapshot | null>(null);
  const [participations, setParticipations] = useState<Participation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);

  // Local editable copy of the config — mutated by the form inputs.
  const [draft, setDraft] = useState<Partial<MissionConfig>>({});

  // ────────────────────────────────────────────────────────────────
  // Auth gate
  // ────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!token) {
      toast.error("Admin session required");
      navigate("/admin");
    }
  }, [token, navigate]);

  // ────────────────────────────────────────────────────────────────
  // Data load
  // ────────────────────────────────────────────────────────────────
  const refresh = useCallback(async (): Promise<void> => {
    if (!token) return;
    setLoading(true);
    try {
      const [snap, parts] = await Promise.all([
        adminGetSnapshot(token),
        adminListParticipations(token),
      ]);
      setSnapshot(snap);
      setDraft(snap.config);
      setParticipations(parts.participations);
    } catch (e) {
      toast.error("Failed to load Command Center data");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) refresh();
  }, [token, refresh]);

  // ────────────────────────────────────────────────────────────────
  // Save handlers (per-section so each save is atomic + intentional)
  // ────────────────────────────────────────────────────────────────
  const saveGiveawayParams = async (): Promise<void> => {
    if (!token) return;
    setSaving(true);
    try {
      await adminUpdateConfig(token, {
        giveaway_draw_date_iso: draft.giveaway_draw_date_iso,
        giveaway_snapshot_date_iso: draft.giveaway_snapshot_date_iso,
        giveaway_reward_sol: draft.giveaway_reward_sol,
        giveaway_winners_count: draft.giveaway_winners_count,
        giveaway_min_invites: draft.giveaway_min_invites,
        giveaway_min_holding_usd: draft.giveaway_min_holding_usd,
      });
      toast.success("Giveaway parameters saved");
      await refresh();
    } catch (e) {
      toast.error("Save failed — check field values");
    } finally {
      setSaving(false);
    }
  };

  const saveExtractionChamber = async (): Promise<void> => {
    if (!token) return;
    setSaving(true);
    try {
      await adminUpdateConfig(token, {
        extraction_chamber_title_fr: draft.extraction_chamber_title_fr ?? null,
        extraction_chamber_title_en: draft.extraction_chamber_title_en ?? null,
        extraction_chamber_subtitle_fr: draft.extraction_chamber_subtitle_fr ?? null,
        extraction_chamber_subtitle_en: draft.extraction_chamber_subtitle_en ?? null,
        extraction_chamber_body_fr: draft.extraction_chamber_body_fr ?? null,
        extraction_chamber_body_en: draft.extraction_chamber_body_en ?? null,
      });
      toast.success("Extraction Chamber copy saved");
      await refresh();
    } catch (e) {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  const saveMissionOverride = async (
    missionId: string,
    patch: Partial<PerMissionOverride>
  ): Promise<void> => {
    if (!token || !draft.missions) return;
    setSaving(true);
    try {
      const next = {
        ...draft.missions,
        [missionId]: { ...draft.missions[missionId], ...patch },
      };
      await adminUpdateConfig(token, { missions: next });
      toast.success(`Mission ${missionId} updated`);
      await refresh();
    } catch (e) {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  const saveEmailToggles = async (): Promise<void> => {
    if (!token) return;
    setSaving(true);
    try {
      await adminUpdateConfig(token, {
        emails_enabled: draft.emails_enabled,
        emails_helius_auto_send: draft.emails_helius_auto_send,
        emails_sender_name: draft.emails_sender_name,
      });
      toast.success("Email automation settings saved");
      await refresh();
    } catch (e) {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  // ────────────────────────────────────────────────────────────────
  // Illustration actions — Sprint 21.1
  // Generation has been removed: we now reuse the bundled artwork at
  // /missions/mission_{id}.jpg. The Command Center only displays which
  // mission has its bundled asset present (always true for the 6
  // canonical missions, modulo file system mishaps).
  // ────────────────────────────────────────────────────────────────
  const resend = async (participationId: string): Promise<void> => {
    if (!token) return;
    try {
      const out = await adminResendParticipationEmail(token, participationId);
      if (out.ok) {
        toast.success("Email re-sent");
      } else {
        toast.error("Resend failed");
      }
      await refresh();
    } catch (e) {
      toast.error("Resend failed");
    }
  };

  // ────────────────────────────────────────────────────────────────
  // Render
  // ────────────────────────────────────────────────────────────────
  const counts = snapshot?.participation_counts || {};
  const illustrations = snapshot?.illustrations || {};

  if (loading || !snapshot) {
    return (
      <div className="min-h-screen bg-background text-foreground grid place-items-center">
        <div className="flex items-center gap-3 text-foreground/70">
          <Loader2 className="h-5 w-5 animate-spin" />
          Loading Command Center…
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground" data-testid="admin-missions-command-page">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/85 backdrop-blur border-b border-border">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate("/admin")}
            className="inline-flex items-center gap-2 text-foreground/70 hover:text-foreground"
            data-testid="back-to-admin-btn"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="font-mono text-xs uppercase tracking-[0.22em]">Admin</span>
          </button>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-[0.22em] border-amber-500/45 text-amber-300/95">
              <Settings className="h-3 w-3 mr-1" />
              Mission Command Center
            </Badge>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={refresh}
              className="gap-1.5"
              data-testid="refresh-snapshot-btn"
            >
              <RefreshCcw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-12">
        {/* SECTION 1 — Giveaway parameters */}
        <section data-testid="section-giveaway">
          <SectionHeader
            kicker="01 · GIVEAWAY"
            title="Giveaway parameters"
            subtitle="Draw date, snapshot date, reward pool, eligibility rules."
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Draw date (UTC)">
              <Input
                type="datetime-local"
                value={isoToInput(draft.giveaway_draw_date_iso || "")}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    giveaway_draw_date_iso: inputToIso(e.target.value),
                  }))
                }
                data-testid="input-draw-date"
              />
            </Field>
            <Field label="Snapshot date (UTC)">
              <Input
                type="datetime-local"
                value={isoToInput(draft.giveaway_snapshot_date_iso || "")}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    giveaway_snapshot_date_iso: inputToIso(e.target.value),
                  }))
                }
                data-testid="input-snapshot-date"
              />
            </Field>
            <Field label="Reward (SOL)">
              <Input
                type="number"
                step="0.01"
                min="0"
                value={draft.giveaway_reward_sol ?? 0}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    giveaway_reward_sol: parseFloat(e.target.value) || 0,
                  }))
                }
                data-testid="input-reward-sol"
              />
            </Field>
            <Field label="Winners">
              <Input
                type="number"
                step="1"
                min="0"
                value={draft.giveaway_winners_count ?? 0}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    giveaway_winners_count: parseInt(e.target.value) || 0,
                  }))
                }
                data-testid="input-winners-count"
              />
            </Field>
            <Field label="Min invites">
              <Input
                type="number"
                step="1"
                min="0"
                value={draft.giveaway_min_invites ?? 0}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    giveaway_min_invites: parseInt(e.target.value) || 0,
                  }))
                }
                data-testid="input-min-invites"
              />
            </Field>
            <Field label="Min holding ($DEEP, USD)">
              <Input
                type="number"
                step="1"
                min="0"
                value={draft.giveaway_min_holding_usd ?? 0}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    giveaway_min_holding_usd: parseFloat(e.target.value) || 0,
                  }))
                }
                data-testid="input-min-holding"
              />
            </Field>
          </div>
          <SectionSaveRow onSave={saveGiveawayParams} saving={saving} testid="save-giveaway-btn" />
        </section>

        {/* SECTION 2 — Extraction Chamber */}
        <section data-testid="section-extraction-chamber">
          <SectionHeader
            kicker="02 · EXTRACTION CHAMBER"
            title="Custom copy (FR + EN)"
            subtitle="Leave a field empty to fall back to the i18n bundle default."
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Title (FR)">
              <Input
                value={draft.extraction_chamber_title_fr || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    extraction_chamber_title_fr: e.target.value || null,
                  }))
                }
                placeholder="(default i18n)"
                data-testid="input-chamber-title-fr"
              />
            </Field>
            <Field label="Title (EN)">
              <Input
                value={draft.extraction_chamber_title_en || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    extraction_chamber_title_en: e.target.value || null,
                  }))
                }
                placeholder="(default i18n)"
                data-testid="input-chamber-title-en"
              />
            </Field>
            <Field label="Subtitle (FR)">
              <Input
                value={draft.extraction_chamber_subtitle_fr || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    extraction_chamber_subtitle_fr: e.target.value || null,
                  }))
                }
                placeholder="(default i18n)"
                data-testid="input-chamber-subtitle-fr"
              />
            </Field>
            <Field label="Subtitle (EN)">
              <Input
                value={draft.extraction_chamber_subtitle_en || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({
                    ...d,
                    extraction_chamber_subtitle_en: e.target.value || null,
                  }))
                }
                placeholder="(default i18n)"
                data-testid="input-chamber-subtitle-en"
              />
            </Field>
            <Field label="Body (FR)" full>
              <Textarea
                rows={3}
                value={draft.extraction_chamber_body_fr || ""}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setDraft((d) => ({
                    ...d,
                    extraction_chamber_body_fr: e.target.value || null,
                  }))
                }
                placeholder="(default i18n)"
                data-testid="input-chamber-body-fr"
              />
            </Field>
            <Field label="Body (EN)" full>
              <Textarea
                rows={3}
                value={draft.extraction_chamber_body_en || ""}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setDraft((d) => ({
                    ...d,
                    extraction_chamber_body_en: e.target.value || null,
                  }))
                }
                placeholder="(default i18n)"
                data-testid="input-chamber-body-en"
              />
            </Field>
          </div>
          <SectionSaveRow onSave={saveExtractionChamber} saving={saving} testid="save-chamber-btn" />
        </section>

        {/* SECTION 3 — Per-mission overrides */}
        <section data-testid="section-missions">
          <SectionHeader
            kicker="03 · MISSIONS"
            title="Per-mission overrides"
            subtitle="Status, custom CTA URL (Telegram override), illustration health."
          />
          <div className="grid grid-cols-1 gap-3">
            {KNOWN_MISSION_IDS.map((mid) => {
              const m = (draft.missions || {})[mid] || {
                status: "live",
                cta_url: null,
                label_date_iso: null,
              };
              const illust = illustrations[mid];
              const partCount = counts[mid] || 0;
              return (
                <div
                  key={mid}
                  className="rounded-lg border border-border bg-card/40 p-4"
                  data-testid={`mission-override-row-${mid}`}
                >
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-center">
                    <div className="lg:col-span-2">
                      <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
                        Mission
                      </div>
                      <div className="font-display font-semibold text-sm mt-1">{mid}</div>
                      <div className="font-mono text-[10px] text-foreground/55 mt-0.5">
                        {partCount} {partCount === 1 ? "participation" : "participations"}
                      </div>
                    </div>
                    <div className="lg:col-span-2">
                      <Label className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
                        Status
                      </Label>
                      <Select
                        value={m.status}
                        onValueChange={(v: string) =>
                          setDraft((d) => ({
                            ...d,
                            missions: {
                              ...(d.missions || {}),
                              [mid]: { ...m, status: v as PerMissionOverride["status"] },
                            },
                          }))
                        }
                      >
                        <SelectTrigger
                          className="mt-1 h-9"
                          data-testid={`select-status-${mid}`}
                        >
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="live">live</SelectItem>
                          <SelectItem value="redacted">redacted</SelectItem>
                          <SelectItem value="completed">completed</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="lg:col-span-5">
                      <Label className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
                        CTA URL (override Telegram)
                      </Label>
                      <Input
                        value={m.cta_url || ""}
                        placeholder="https://t.me/deepotus (default)"
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setDraft((d) => ({
                            ...d,
                            missions: {
                              ...(d.missions || {}),
                              [mid]: { ...m, cta_url: e.target.value || null },
                            },
                          }))
                        }
                        className="mt-1 h-9 font-mono text-xs"
                        data-testid={`input-cta-url-${mid}`}
                      />
                    </div>
                    <div className="lg:col-span-3 flex flex-col gap-1.5">
                      <div className="flex items-center gap-2 text-[11px] text-foreground/65">
                        {illust?.present ? (
                          <>
                            {/* Thumbnail of the bundled artwork so admin
                                can confirm at a glance which image will
                                be embedded in outgoing emails. */}
                            <img
                              src={illust.public_path}
                              alt={`mission_${mid} illustration`}
                              className="h-10 w-10 rounded-sm object-cover border border-border/60"
                              loading="lazy"
                              data-testid={`mission-illust-thumb-${mid}`}
                            />
                            <span className="flex flex-col">
                              <span className="flex items-center gap-1">
                                <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                                <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-300/95">
                                  bundled
                                </span>
                              </span>
                              <span className="font-mono text-[10px] text-foreground/55 tabular-nums">
                                {(illust.size_bytes / 1024).toFixed(0)} KB
                              </span>
                            </span>
                          </>
                        ) : (
                          <span className="flex items-center gap-1.5">
                            <ImageIcon className="h-3.5 w-3.5 text-foreground/45" />
                            <AlertTriangle className="h-3 w-3 text-amber-400" />
                            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-300/85">
                              missing asset
                            </span>
                          </span>
                        )}
                        <Button
                          type="button"
                          size="sm"
                          onClick={() =>
                            saveMissionOverride(mid, {
                              status: m.status,
                              cta_url: m.cta_url,
                            })
                          }
                          disabled={saving}
                          data-testid={`save-mission-${mid}-btn`}
                          className="ml-auto bg-amber-500/95 hover:bg-amber-500 text-zinc-950"
                        >
                          Save
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* SECTION 4 — Email automation + Participations */}
        <section data-testid="section-emails">
          <SectionHeader
            kicker="04 · EMAILS & BUNDLED ILLUSTRATIONS"
            title="Resend automation"
            subtitle="Master switch + recent participations + manual resend. Emails embed the bundled mission artwork (/missions/mission_{id}.jpg)."
          />
          <div className="rounded-lg border border-border bg-card/40 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
                  Emails on participation
                </div>
                <div className="text-xs text-foreground/70 mt-0.5">
                  When ON, every form submit triggers a templated Resend email.
                </div>
              </div>
              <Switch
                checked={!!draft.emails_enabled}
                onCheckedChange={(v: boolean) =>
                  setDraft((d) => ({ ...d, emails_enabled: v }))
                }
                data-testid="switch-emails-enabled"
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
                  Helius auto-trigger (post-mint)
                </div>
                <div className="text-xs text-foreground/70 mt-0.5">
                  Sends a mission email when Helius detects a new $DEEP holder
                  whose wallet matches an existing email.
                </div>
              </div>
              <Switch
                checked={!!draft.emails_helius_auto_send}
                onCheckedChange={(v: boolean) =>
                  setDraft((d) => ({ ...d, emails_helius_auto_send: v }))
                }
                data-testid="switch-emails-helius"
              />
            </div>
            <Field label="Sender name (From header)">
              <Input
                value={draft.emails_sender_name || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft((d) => ({ ...d, emails_sender_name: e.target.value }))
                }
                placeholder="Cabinet ΔΣ · DEEPOTUS"
                data-testid="input-sender-name"
              />
            </Field>
            <SectionSaveRow
              onSave={saveEmailToggles}
              saving={saving}
              testid="save-emails-btn"
            />
          </div>

          {/* Participations list */}
          <div
            className="mt-6 rounded-lg border border-border bg-card/40 overflow-hidden"
            data-testid="participations-table"
          >
            <div className="px-4 py-3 border-b border-border/60 flex items-center justify-between">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
                Recent participations ({participations.length})
              </div>
              <Badge variant="outline" className="font-mono text-[9px] uppercase tracking-[0.22em]">
                <Mail className="h-3 w-3 mr-1" /> Last 200
              </Badge>
            </div>
            <div className="divide-y divide-border/40 max-h-[420px] overflow-y-auto">
              {participations.length === 0 && (
                <div className="px-4 py-6 text-sm text-foreground/55 italic">
                  No participations yet.
                </div>
              )}
              {participations.map((p) => (
                <div
                  key={p._id}
                  className="px-4 py-3 grid grid-cols-1 sm:grid-cols-12 gap-2 items-center text-xs"
                  data-testid={`participation-row-${p._id}`}
                >
                  <div className="sm:col-span-3 font-mono text-foreground/85 truncate">{p.email}</div>
                  <div className="sm:col-span-2 font-mono text-foreground/60">{p.mission_id}</div>
                  <div className="sm:col-span-2 font-mono text-foreground/55 truncate">
                    {p.wallet_address ? `${p.wallet_address.slice(0, 8)}…` : "—"}
                  </div>
                  <div className="sm:col-span-2 font-mono text-foreground/55">
                    {p.source}
                  </div>
                  <div className="sm:col-span-1">
                    {p.email_sent ? (
                      <Badge variant="outline" className="font-mono text-[9px] uppercase tracking-[0.18em] border-emerald-500/45 text-emerald-300">
                        sent
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="font-mono text-[9px] uppercase tracking-[0.18em] border-amber-500/45 text-amber-300">
                        pending
                      </Badge>
                    )}
                  </div>
                  <div className="sm:col-span-2 flex justify-end">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => resend(p._id)}
                      className="gap-1.5 h-7 text-xs"
                      data-testid={`resend-${p._id}-btn`}
                    >
                      <Send className="h-3 w-3" />
                      Resend
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Last updated footer */}
        {snapshot.config.updated_at && (
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/40 text-right">
            Last updated: {new Date(snapshot.config.updated_at).toLocaleString()} ·{" "}
            {snapshot.config.updated_by || "system"}
          </div>
        )}
      </main>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// Local helpers (kept in the same file — tiny, single-use)
// ────────────────────────────────────────────────────────────────────
interface FieldProps {
  label: string;
  full?: boolean;
  children: React.ReactNode;
}
function Field({ label, full, children }: FieldProps): JSX.Element {
  return (
    <div className={full ? "sm:col-span-2" : ""}>
      <Label className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
        {label}
      </Label>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}

interface SectionHeaderProps {
  kicker: string;
  title: string;
  subtitle?: string;
}
function SectionHeader({ kicker, title, subtitle }: SectionHeaderProps): JSX.Element {
  return (
    <div className="mb-5">
      <div className="font-mono text-[10px] uppercase tracking-[0.30em] text-amber-300/85">
        {kicker}
      </div>
      <h2 className="mt-1.5 font-display font-semibold text-xl tracking-tight">{title}</h2>
      {subtitle && <p className="mt-1 text-sm text-foreground/65 max-w-prose">{subtitle}</p>}
    </div>
  );
}

interface SaveRowProps {
  onSave: () => Promise<void> | void;
  saving: boolean;
  testid: string;
}
function SectionSaveRow({ onSave, saving, testid }: SaveRowProps): JSX.Element {
  return (
    <div className="mt-4 flex justify-end">
      <Button
        type="button"
        onClick={onSave}
        disabled={saving}
        className="gap-2 bg-amber-500/95 hover:bg-amber-500 text-zinc-950"
        data-testid={testid}
      >
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <ExternalLink className="h-4 w-4" />}
        Save section
      </Button>
    </div>
  );
}
