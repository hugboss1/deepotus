/**
 * AdminCadenceSection — "Cadence" tab inside AdminBots.
 *
 * Sprint 18 (TASK 8) — gives the admin one place to:
 *   1. Configure the daily fixed-time posting schedule per platform
 *      (X / Telegram). Up to 8 UTC time slots each, with an optional
 *      multi-select of V2 archetype ids the scheduler may pick from
 *      when that slot fires (empty = all archetypes allowed).
 *   2. Configure reactive triggers (whale buys, holder milestones,
 *      market-cap milestones). Persisted now; wired into the
 *      scheduler in a follow-up sprint.
 *   3. Configure quiet hours — a UTC window during which all bot
 *      jobs stay silent. Window may wrap past midnight.
 *
 * Self-contained: owns its own state + API calls. Parent (AdminBots)
 * only mounts `<AdminCadenceSection api={API} headers={headers} />`.
 *
 * All inputs persist on blur via `PUT /api/admin/bots/config` with
 * partial-merge semantics (every patch leaves untouched fields alone).
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import type { AxiosRequestHeaders } from "axios";
import {
  Calendar,
  Clock,
  Plus,
  Sparkles,
  Trash2,
  TrendingUp,
  Twitter,
  Send as TelegramIcon,
  Moon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { logger } from "@/lib/logger";

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------
interface DailyScheduleEntry {
  enabled: boolean;
  post_times_utc: string[];
  archetypes: string[];
}

interface CadenceShape {
  daily_schedule: {
    x: DailyScheduleEntry;
    telegram: DailyScheduleEntry;
  };
  reactive_triggers: {
    enabled: boolean;
    whale_buy_min_sol: number;
    holder_milestones: number[];
    marketcap_milestones_usd: number[];
  };
  quiet_hours: {
    enabled: boolean;
    start_utc: string;
    end_utc: string;
  };
}

interface V2Template {
  id: string;
  weight: number;
  label_fr: string;
  label_en: string;
}

interface Props {
  api: string;
  headers: AxiosRequestHeaders;
}

const HHMM_RE = /^\d{2}:\d{2}$/;

// ---------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------
export default function AdminCadenceSection({ api, headers }: Props) {
  const [cadence, setCadence] = useState<CadenceShape | null>(null);
  const [templates, setTemplates] = useState<V2Template[]>([]);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [{ data: cfg }, { data: tpls }] = await Promise.all([
        axios.get(`${api}/api/admin/bots/config`, { headers }),
        axios.get(`${api}/api/admin/bots/v2-templates`, { headers }),
      ]);
      setCadence(cfg?.cadence || null);
      setTemplates(Array.isArray(tpls) ? tpls : []);
    } catch (err) {
      logger.error(err);
      toast.error("Could not load cadence config");
    }
  }, [api, headers]);

  useEffect(() => {
    load();
  }, [load]);

  // -------------------------------------------------------------------
  // Persist a partial cadence patch
  // -------------------------------------------------------------------
  const persist = useCallback(
    async (patch: Record<string, unknown>, successMsg?: string) => {
      setBusy(true);
      try {
        const { data } = await axios.put(
          `${api}/api/admin/bots/config`,
          { cadence: patch },
          { headers },
        );
        setCadence(data?.cadence || null);
        if (successMsg) toast.success(successMsg);
      } catch (err) {
        logger.error(err);
        const msg =
          // eslint-disable-next-line
          (err as any)?.response?.data?.detail || "Cadence update failed";
        toast.error(typeof msg === "string" ? msg : "Cadence update failed");
      } finally {
        setBusy(false);
      }
    },
    [api, headers],
  );

  if (!cadence) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 text-sm text-muted-foreground">
        Loading cadence configuration…
      </div>
    );
  }

  return (
    <div className="space-y-5" data-testid="cadence-section">
      {/* ============================================================ */}
      {/*  Daily schedule                                              */}
      {/* ============================================================ */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <div className="flex items-start gap-2">
          <Calendar size={16} className="text-muted-foreground mt-0.5" />
          <div className="flex-1">
            <div className="font-display font-semibold">Daily schedule</div>
            <p className="text-xs text-muted-foreground mt-0.5">
              UTC time slots. Each slot fires one Prophet post on the platform.
              Up to 8 slots per platform per day. Use "Allowed archetypes" to
              restrict which V2 templates are eligible at that slot — leave
              empty to allow all.
            </p>
          </div>
        </div>

        <PlatformDailySchedule
          platform="x"
          icon={<Twitter size={16} className="text-[#1DA1F2]" />}
          label="X / Twitter"
          entry={cadence.daily_schedule.x}
          templates={templates}
          busy={busy}
          onSave={(patch) =>
            persist(
              { daily_schedule: { x: patch } },
              "X schedule saved",
            )
          }
        />

        <PlatformDailySchedule
          platform="telegram"
          icon={<TelegramIcon size={16} className="text-[#2AABEE]" />}
          label="Telegram"
          entry={cadence.daily_schedule.telegram}
          templates={templates}
          busy={busy}
          onSave={(patch) =>
            persist(
              { daily_schedule: { telegram: patch } },
              "Telegram schedule saved",
            )
          }
        />
      </div>

      {/* ============================================================ */}
      {/*  Reactive triggers                                           */}
      {/* ============================================================ */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <div className="flex items-start gap-2">
          <TrendingUp size={16} className="text-muted-foreground mt-0.5" />
          <div className="flex-1">
            <div className="font-display font-semibold">Reactive triggers</div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Fire an extra Prophet post when on-chain or community events
              cross thresholds. Persisted now — wiring into the scheduler is a
              follow-up sprint, so toggling this switch only stages the config.
            </p>
          </div>
          <Switch
            checked={cadence.reactive_triggers.enabled}
            onCheckedChange={(v) =>
              persist(
                { reactive_triggers: { enabled: v } },
                `Reactive triggers ${v ? "enabled" : "disabled"}`,
              )
            }
            data-testid="cadence-reactive-toggle"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <NumberKnob
            label="Whale buy min (SOL)"
            testId="cadence-whale-min"
            value={cadence.reactive_triggers.whale_buy_min_sol}
            min={0}
            step={0.5}
            onCommit={(n) =>
              persist(
                { reactive_triggers: { whale_buy_min_sol: n } },
                "Whale threshold saved",
              )
            }
          />

          <NumberListEditor
            label="Holder milestones"
            testId="cadence-holder-milestones"
            values={cadence.reactive_triggers.holder_milestones}
            placeholder="100,500,1000…"
            onCommit={(arr) =>
              persist(
                { reactive_triggers: { holder_milestones: arr } },
                "Holder milestones saved",
              )
            }
          />

          <NumberListEditor
            label="Market-cap milestones (USD)"
            testId="cadence-marketcap-milestones"
            values={cadence.reactive_triggers.marketcap_milestones_usd}
            placeholder="50000,100000,250000…"
            onCommit={(arr) =>
              persist(
                {
                  reactive_triggers: { marketcap_milestones_usd: arr },
                },
                "Marketcap milestones saved",
              )
            }
          />
        </div>
      </div>

      {/* ============================================================ */}
      {/*  Quiet hours                                                 */}
      {/* ============================================================ */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <div className="flex items-start gap-2">
          <Moon size={16} className="text-muted-foreground mt-0.5" />
          <div className="flex-1">
            <div className="font-display font-semibold">Quiet hours (UTC)</div>
            <p className="text-xs text-muted-foreground mt-0.5">
              All bot jobs stay silent inside this window. If start &gt; end
              the window wraps past midnight (e.g. 23:00 → 06:00).
            </p>
          </div>
          <Switch
            checked={cadence.quiet_hours.enabled}
            onCheckedChange={(v) =>
              persist(
                { quiet_hours: { enabled: v } },
                `Quiet hours ${v ? "enabled" : "disabled"}`,
              )
            }
            data-testid="cadence-quiet-toggle"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <TimeKnob
            label="Start (UTC)"
            testId="cadence-quiet-start"
            value={cadence.quiet_hours.start_utc}
            onCommit={(s) =>
              persist({ quiet_hours: { start_utc: s } }, "Quiet start saved")
            }
          />
          <TimeKnob
            label="End (UTC)"
            testId="cadence-quiet-end"
            value={cadence.quiet_hours.end_utc}
            onCommit={(s) =>
              persist({ quiet_hours: { end_utc: s } }, "Quiet end saved")
            }
          />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------
// PlatformDailySchedule — one platform row in the daily schedule card
// ---------------------------------------------------------------------
interface PlatformDailySchedulePropsT {
  platform: "x" | "telegram";
  icon: React.ReactNode;
  label: string;
  entry: DailyScheduleEntry;
  templates: V2Template[];
  busy: boolean;
  onSave: (patch: Partial<DailyScheduleEntry>) => void;
}

function PlatformDailySchedule({
  platform,
  icon,
  label,
  entry,
  templates,
  busy,
  onSave,
}: PlatformDailySchedulePropsT) {
  const [draftSlot, setDraftSlot] = useState<string>("");

  const addSlot = () => {
    const s = (draftSlot || "").trim();
    if (!HHMM_RE.test(s)) {
      toast.error("Use HH:MM (UTC)");
      return;
    }
    if (entry.post_times_utc.includes(s)) return;
    if (entry.post_times_utc.length >= 8) {
      toast.error("Max 8 slots per day");
      return;
    }
    const next = [...entry.post_times_utc, s].sort();
    setDraftSlot("");
    onSave({ post_times_utc: next });
  };

  const removeSlot = (slot: string) => {
    onSave({ post_times_utc: entry.post_times_utc.filter((s) => s !== slot) });
  };

  const toggleArchetype = (id: string) => {
    const has = entry.archetypes.includes(id);
    const next = has
      ? entry.archetypes.filter((x) => x !== id)
      : [...entry.archetypes, id];
    onSave({ archetypes: next });
  };

  return (
    <div
      className="p-3 rounded-lg border border-border/60 bg-background/40 space-y-3"
      data-testid={`cadence-daily-${platform}`}
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <Label className="font-medium text-sm flex items-center gap-2">
          {icon}
          {label}
        </Label>
        <Switch
          checked={entry.enabled}
          onCheckedChange={(v) => onSave({ enabled: v })}
          data-testid={`cadence-daily-${platform}-toggle`}
        />
      </div>

      {/* Time slots */}
      <div>
        <Label className="text-[10px] uppercase tracking-widest text-muted-foreground">
          Time slots (UTC)
        </Label>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {entry.post_times_utc.length === 0 && (
            <span className="text-xs text-muted-foreground italic">
              No slots configured.
            </span>
          )}
          {entry.post_times_utc.map((slot) => (
            <Badge
              key={slot}
              variant="outline"
              className="font-mono pl-2.5 pr-1 py-0 h-7 gap-1 border-foreground/30"
              data-testid={`cadence-slot-${platform}-${slot}`}
            >
              {slot}
              <button
                type="button"
                aria-label={`Remove ${slot}`}
                disabled={busy}
                onClick={() => removeSlot(slot)}
                className="ml-1 inline-flex items-center justify-center w-5 h-5 rounded hover:bg-foreground/10 text-muted-foreground hover:text-foreground"
              >
                <Trash2 size={11} />
              </button>
            </Badge>
          ))}
        </div>
        <div className="mt-2 flex items-center gap-2">
          <Input
            type="time"
            value={draftSlot}
            onChange={(e) => setDraftSlot(e.target.value)}
            className="w-32 h-8 font-mono text-sm"
            data-testid={`cadence-daily-${platform}-time-input`}
          />
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={addSlot}
            disabled={busy || entry.post_times_utc.length >= 8}
            data-testid={`cadence-daily-${platform}-add-slot`}
          >
            <Plus size={13} className="mr-1" /> Add slot
          </Button>
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {entry.post_times_utc.length}/8
          </span>
        </div>
      </div>

      {/* Archetypes whitelist */}
      <div>
        <Label className="text-[10px] uppercase tracking-widest text-muted-foreground">
          Allowed archetypes (V2)
        </Label>
        <p className="text-[11px] text-muted-foreground mt-1 mb-2">
          Empty list ⇒ scheduler may pick any of the 5 templates (weighted random).
        </p>
        <div className="flex flex-wrap gap-2">
          {templates.map((t) => {
            const active = entry.archetypes.includes(t.id);
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => toggleArchetype(t.id)}
                disabled={busy}
                className={`text-[11px] font-mono uppercase tracking-widest px-2 py-1 rounded border transition-colors ${
                  active
                    ? "border-[#33FF33]/50 bg-[#33FF33]/10 text-[#33FF33]"
                    : "border-border/60 bg-background/60 text-muted-foreground hover:border-foreground/30"
                }`}
                data-testid={`cadence-archetype-${platform}-${t.id}`}
                aria-pressed={active}
              >
                {t.id} <span className="opacity-50">·{t.weight}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------
// Small reusable inputs
// ---------------------------------------------------------------------
function NumberKnob({
  label,
  testId,
  value,
  min,
  step,
  onCommit,
}: {
  label: string;
  testId: string;
  value: number;
  min?: number;
  step?: number;
  onCommit: (n: number) => void;
}) {
  const [draft, setDraft] = useState<string>(String(value));
  useEffect(() => setDraft(String(value)), [value]);
  return (
    <div>
      <Label className="text-[10px] uppercase tracking-widest text-muted-foreground">
        {label}
      </Label>
      <Input
        type="number"
        min={min}
        step={step ?? 1}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => {
          const n = Number(draft);
          if (!Number.isNaN(n)) onCommit(n);
        }}
        className="mt-1 h-8 font-mono text-sm"
        data-testid={testId}
      />
    </div>
  );
}

function TimeKnob({
  label,
  testId,
  value,
  onCommit,
}: {
  label: string;
  testId: string;
  value: string;
  onCommit: (s: string) => void;
}) {
  const [draft, setDraft] = useState<string>(value);
  useEffect(() => setDraft(value), [value]);
  return (
    <div>
      <Label className="text-[10px] uppercase tracking-widest text-muted-foreground">
        {label}
      </Label>
      <Input
        type="time"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => {
          if (HHMM_RE.test(draft)) onCommit(draft);
        }}
        className="mt-1 h-8 font-mono text-sm w-full sm:w-32"
        data-testid={testId}
      />
    </div>
  );
}

function NumberListEditor({
  label,
  testId,
  values,
  placeholder,
  onCommit,
}: {
  label: string;
  testId: string;
  values: number[];
  placeholder?: string;
  onCommit: (arr: number[]) => void;
}) {
  const initialDraft = useMemo(() => values.join(","), [values]);
  const [draft, setDraft] = useState<string>(initialDraft);
  useEffect(() => setDraft(initialDraft), [initialDraft]);
  return (
    <div>
      <Label className="text-[10px] uppercase tracking-widest text-muted-foreground">
        {label}
      </Label>
      <Input
        type="text"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder={placeholder}
        onBlur={() => {
          const arr = draft
            .split(/[,\s]+/)
            .map((s) => Number(String(s).trim()))
            .filter((n) => Number.isFinite(n) && n > 0);
          onCommit(arr);
        }}
        className="mt-1 h-8 font-mono text-sm"
        data-testid={testId}
      />
    </div>
  );
}
