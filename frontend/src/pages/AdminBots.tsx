import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { getAdminToken, setAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { toast } from "sonner";
import {
  ArrowLeft,
  RefreshCcw,
  Bot,
  Power,
  Twitter,
  Send as TelegramIcon,
  Sparkles,
  PlayCircle,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Activity,
  Settings,
  TrendingUp,
  Wand2,
  Languages,
  Image as ImageIcon,
  Download,
  Newspaper,
  ShieldCheck,
  CalendarClock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { logger } from "@/lib/logger";
import LoyaltySection from "@/pages/admin/sections/LoyaltySection";
import NewsRepostSection from "@/pages/admin/sections/NewsRepostSection";
import NewsFeedSection from "@/pages/admin/sections/NewsFeedSection";
import AdminCadenceSection from "@/pages/admin/sections/AdminCadenceSection";
import AdminJobsSection from "@/pages/admin/sections/AdminJobsSection";
import AdminLogsSection from "@/pages/admin/sections/AdminLogsSection";
import AdminPreviewSection from "@/pages/admin/sections/AdminPreviewSection";
import CustomLlmKeysSection from "@/pages/admin/sections/CustomLlmKeysSection";

const API = process.env.REACT_APP_BACKEND_URL;

const CONTENT_TYPE_ICONS: Record<string, string> = {
  prophecy: "🔮",
  market_commentary: "📉",
  vault_update: "🔒",
  kol_reply: "🕶️",
};

const STATUS_COLOR: Record<string, string> = {
  heartbeat: "#18C964",
  posted: "#2DD4BF",
  killed: "#E11D48",
  skipped: "#F59E0B",
  failed: "#E11D48",
};

const LLM_PRESETS = [
  { id: "claude-sonnet", label: "Claude Sonnet 4.5 (Anthropic)", provider: "anthropic", model: "claude-sonnet-4-5-20250929" },
  { id: "gpt-4o", label: "GPT-4o (OpenAI)", provider: "openai", model: "gpt-4o" },
  { id: "gpt-5", label: "GPT-5 (OpenAI)", provider: "openai", model: "gpt-5" },
  { id: "gemini-2-5-pro", label: "Gemini 2.5 Pro (Google)", provider: "gemini", model: "gemini-2.5-pro" },
];

/**
 * AdminBots — Prophet fleet control dashboard.
 *
 * Sprint 22 — migrated `.jsx` → `.tsx`. Type strictness is intentionally
 * soft for this file (tsconfig has `strict: false` / `noImplicitAny:
 * false`) because most of the React state here is a single big mutable
 * config object that's already validated by the Pydantic schema on the
 * backend. We keep top-level interfaces (BotConfig, ContentTypeMeta)
 * to lock the shape that matters, and leave inner sub-doc state as
 * implicit `any` until a future hardening pass.
 */
interface ContentTypeMeta {
  id: string;
  label_en: string;
  description_en: string;
}

// eslint-disable-next-line
type BotConfig = any; // Pydantic-validated server-side; loose on the FE.

export default function AdminBots() {
  const navigate = useNavigate();
  const [token] = useState<string | null>(() => getAdminToken());
  const [config, setConfig] = useState<BotConfig | null>(null);
  const [contentTypes, setContentTypes] = useState<ContentTypeMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  // Preview / V2 / image state moved to <AdminPreviewSection /> in Sprint 21.
  // Jobs + Logs (post_attempts) state moved to their respective sections —
  // each section owns its own polling + filter state for fault isolation.

  // ---- News-feed aggregator state (Config tab "News Feed" section) ----
  // News feed state has moved to <NewsFeedSection /> (Sprint 6 split).
  // It now owns its own state, draft inputs, and refresh API call.

  // Loyalty + News-repost have moved to dedicated TSX section components
  // (Sprint 5 split). They own their state and API calls — see
  // /pages/admin/sections/{LoyaltySection,NewsRepostSection}.tsx.

  // ---- Custom LLM keys vault ----
  // The whole UI (provider cards + set/rotate dialog + handlers) has
  // moved to <CustomLlmKeysSection /> (Sprint 22.3 split). This parent
  // only passes `config` + `loadConfig` so the card statuses refresh
  // after a mutation.

  // Filters for post log moved to <AdminLogsSection />.

  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);

  useEffect(() => {
    if (!token) {
      navigate("/admin");
      return;
    }
    bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync the news-feed text-area drafts has moved into <NewsFeedSection />.
  // (Sprint 6 split — see /pages/admin/sections/NewsFeedSection.tsx.)

  async function bootstrap() {
    try {
      await Promise.all([loadConfig(), loadContentTypes()]);
    } finally {
      setLoading(false);
    }
  }

  async function loadConfig() {
    try {
      const { data } = await axios.get(`${API}/api/admin/bots/config`, { headers });
      setConfig(data);
    } catch (err) {
      if (err?.response?.status === 401) {
        clearAdminToken();
        navigate("/admin");
        return;
      }
      logger.error(err);
      toast.error("Could not load bot config");
    }
  }

  async function loadContentTypes() {
    try {
      const { data } = await axios.get(`${API}/api/admin/bots/content-types`, { headers });
      setContentTypes(Array.isArray(data) ? data : []);
    } catch (err) {
      logger.error(err);
    }
  }

  // loadJobs / loadPosts / loadV2Templates moved to their respective sections.
  // loadNews() and refreshNewsNow() moved to <NewsFeedSection /> (Sprint 6 split).

  // openLlmSecretDialog / submitLlmSecret / revokeLlmSecret + the
  // matching dialog state have moved to <CustomLlmKeysSection />
  // (Sprint 22.3 split). The child section owns the full flow and
  // calls `loadConfig()` to refresh the masked status after a mutation.

  async function patchConfig(patch: Record<string, unknown>, successMsg?: string) {
    setBusy(true);
    try {
      const { data } = await axios.put(`${API}/api/admin/bots/config`, patch, { headers });
      setConfig(data);
      if (successMsg) toast.success(successMsg);
      // Jobs section auto-polls every 10 s, no manual refresh needed.
    } catch (err: any) {
      logger.error(err);
      toast.error(err?.response?.data?.detail || "Config update failed");
    } finally {
      setBusy(false);
    }
  }

  async function toggleKillSwitch(active: boolean) {
    setBusy(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/bots/kill-switch`,
        { active },
        { headers },
      );
      setConfig(data);
      toast[active ? "warning" : "success"](
        active ? "Kill-switch ARMED — all bot jobs blocked" : "Kill-switch released — bots live",
      );
      // Jobs section auto-polls every 10 s, no manual refresh needed.
    } catch (err) {
      logger.error(err);
      toast.error("Kill-switch toggle failed");
    } finally {
      setBusy(false);
    }
  }

  async function manualHeartbeat() {
    try {
      await axios.post(`${API}/api/admin/bots/heartbeat`, {}, { headers });
      toast.success("Heartbeat pinged");
      // Logs section auto-polls every 10 s, no manual refresh needed.
    } catch (err) {
      logger.error(err);
      toast.error("Heartbeat failed");
    }
  }

  /**
   * Sprint 17.5 follow-up — dual-mode "Release" button.
   *
   * When the kill-switch is ARMED → release it (legacy behaviour).
   * When the kill-switch is OFF (bots live) → force every registered
   * scheduler job to fire on the next loop iteration so the operator
   * can verify end-to-end without waiting for the next cadence tick.
   * The backend's ``force_run_all_now()`` honours every per-job
   * guard (panic, dispatch_dry_run, per-trigger cooldown), so
   * mashing this button can never push a forbidden post.
   */
  async function releaseAction() {
    if (killOn) {
      // Legacy path — un-arm the kill-switch.
      await toggleKillSwitch(false);
      return;
    }
    setBusy(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/bots/release-now`,
        {},
        { headers },
      );
      const triggered = (data?.triggered as Array<{ id: string }> | undefined) || [];
      if (triggered.length === 0) {
        toast.warning(
          (data?.note as string) || "No jobs to force-run",
        );
      } else {
        toast.success(
          `Forced ${triggered.length} job(s) to run now`,
          {
            description: triggered
              .slice(0, 6)
              .map((t) => t.id)
              .join(" · "),
          },
        );
      }
    } catch (err) {
      // eslint-disable-next-line
      const detail = (err as any)?.response?.data?.detail;
      logger.error(err);
      toast.error(typeof detail === "string" ? detail : "Release-now failed");
    } finally {
      setBusy(false);
    }
  }

  // generatePreview() and downloadPreviewImage() moved to <AdminPreviewSection />
  // along with the entire preview state. (Sprint 21 split.)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center font-mono text-sm text-muted-foreground">
        Booting Prophet fleet control…
      </div>
    );
  }

  const killOn = Boolean(config?.kill_switch_active);
  const currentLlmId = LLM_PRESETS.find(
    (p) => p.provider === config?.llm?.provider && p.model === config?.llm?.model,
  )?.id || "custom";

  return (
    <div className="min-h-screen" data-testid="admin-bots-page">
      {/* Header */}
      <header className="border-b border-border sticky top-0 z-20 bg-background/80 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-3">
          <Button
            asChild
            variant="ghost"
            size="sm"
            className="rounded-[var(--btn-radius)]"
            data-testid="admin-bots-back"
          >
            <Link to="/admin">
              <ArrowLeft size={16} className="mr-1" /> Admin
            </Link>
          </Button>
          <div className="font-display font-semibold tracking-tight flex items-center gap-2">
            <Bot size={18} />
            Prophet Fleet · Bots Control
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Badge
              variant="outline"
              className={`font-mono text-[10px] uppercase tracking-widest ${
                killOn
                  ? "border-[#E11D48]/60 bg-[#E11D48]/10 text-[#E11D48]"
                  : "border-[#18C964]/60 bg-[#18C964]/10 text-[#18C964]"
              }`}
              data-testid="admin-bots-kill-badge"
            >
              {killOn ? "KILL-SWITCH ON" : "LIVE"}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                loadConfig();
              }}
              className="rounded-[var(--btn-radius)]"
              data-testid="admin-bots-refresh"
            >
              <RefreshCcw size={14} />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Kill-switch hero */}
        <section
          className={`rounded-xl border-2 p-5 md:p-6 ${
            killOn
              ? "border-[#E11D48]/50 bg-[#E11D48]/5"
              : "border-[#18C964]/50 bg-[#18C964]/5"
          }`}
          data-testid="admin-bots-kill-hero"
        >
          <div className="flex items-start gap-4 flex-wrap">
            <div
              className={`rounded-full p-3 ${
                killOn ? "bg-[#E11D48]/15" : "bg-[#18C964]/15"
              }`}
            >
              <Power
                size={28}
                className={killOn ? "text-[#E11D48]" : "text-[#18C964]"}
                strokeWidth={2.5}
              />
            </div>
            <div className="flex-1 min-w-[260px]">
              <div
                className={`font-mono text-[10px] uppercase tracking-[0.25em] ${
                  killOn ? "text-[#E11D48]" : "text-[#18C964]"
                }`}
              >
                {killOn ? "⚠ Emergency hold" : "✓ All systems go"}
              </div>
              <h2 className="font-display text-2xl md:text-3xl font-semibold leading-tight mt-1">
                {killOn
                  ? "Bots are muted — no post will go out."
                  : "Bots are live — prophecies will broadcast on schedule."}
              </h2>
              <p className="mt-2 text-sm text-foreground/75 leading-relaxed max-w-2xl">
                Flipping this switch persists instantly to Mongo and every running job checks
                it before acting. Safe to toggle multiple times per second — jobs coalesce.
              </p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <Button
                variant={killOn ? "default" : "outline"}
                size="lg"
                onClick={() => releaseAction()}
                disabled={busy}
                className="rounded-[var(--btn-radius)] btn-press font-semibold"
                data-testid="admin-bots-kill-off"
                title={
                  killOn
                    ? "Release the kill-switch — bots resume on schedule"
                    : "Force every scheduled job to run now (bypasses cadence wait, respects panic + rate limits)"
                }
              >
                <PlayCircle size={18} className="mr-2" />
                {killOn ? "Release" : "Release · Run jobs now"}
              </Button>
              <Button
                variant={killOn ? "outline" : "destructive"}
                size="lg"
                onClick={() => toggleKillSwitch(true)}
                disabled={killOn || busy}
                className="rounded-[var(--btn-radius)] btn-press font-semibold"
                data-testid="admin-bots-kill-on"
              >
                <AlertTriangle size={18} className="mr-2" /> Arm kill-switch
              </Button>
            </div>
          </div>
        </section>

        <Tabs defaultValue="config" className="w-full">
          <TabsList className="grid w-full grid-cols-5 max-w-2xl">
            <TabsTrigger value="config" data-testid="tab-config">
              <Settings size={14} className="mr-1" /> Config
            </TabsTrigger>
            <TabsTrigger value="preview" data-testid="tab-preview">
              <Wand2 size={14} className="mr-1" /> Preview
            </TabsTrigger>
            <TabsTrigger value="cadence" data-testid="tab-cadence">
              <CalendarClock size={14} className="mr-1" /> Cadence
            </TabsTrigger>
            <TabsTrigger value="jobs" data-testid="tab-jobs">
              <Clock size={14} className="mr-1" /> Jobs
            </TabsTrigger>
            <TabsTrigger value="logs" data-testid="tab-logs">
              <Activity size={14} className="mr-1" /> Logs
            </TabsTrigger>
          </TabsList>

          {/* -------------------- CONFIG TAB -------------------- */}
          <TabsContent value="config" className="mt-6 space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Platforms */}
              <div className="rounded-xl border border-border bg-card p-5 space-y-4">
                <div className="flex items-center gap-2">
                  <ShieldAlert size={16} className="text-muted-foreground" />
                  <div className="font-display font-semibold">Platforms</div>
                </div>

                {/* X / Twitter */}
                <div className="flex items-start gap-3 p-3 rounded-lg border border-border/60 bg-background/40">
                  <Twitter size={18} className="text-[#1DA1F2] mt-1" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <Label className="font-medium text-sm">X / Twitter</Label>
                      <Switch
                        checked={Boolean(config?.platforms?.x?.enabled)}
                        onCheckedChange={(v: boolean) =>
                          patchConfig(
                            { platforms: { x: { enabled: v } } },
                            `X bot ${v ? "enabled" : "disabled"}`,
                          )
                        }
                        data-testid="config-platform-x-toggle"
                      />
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <Label className="text-xs text-muted-foreground whitespace-nowrap">
                        Every
                      </Label>
                      <Input
                        type="number"
                        min="1"
                        max="48"
                        value={config?.platforms?.x?.post_frequency_hours ?? 4}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setConfig({
                            ...config,
                            platforms: {
                              ...config.platforms,
                              x: {
                                ...config.platforms.x,
                                post_frequency_hours: Number(e.target.value),
                              },
                            },
                          })
                        }
                        onBlur={(e: React.FocusEvent<HTMLInputElement>) =>
                          patchConfig(
                            {
                              platforms: {
                                x: { post_frequency_hours: Number(e.target.value) },
                              },
                            },
                            "X frequency saved",
                          )
                        }
                        className="w-20 h-8 font-mono text-sm"
                        data-testid="config-platform-x-frequency"
                      />
                      <Label className="text-xs text-muted-foreground">hours</Label>
                    </div>
                  </div>
                </div>

                {/* Telegram */}
                <div className="flex items-start gap-3 p-3 rounded-lg border border-border/60 bg-background/40">
                  <TelegramIcon size={18} className="text-[#2AABEE] mt-1" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <Label className="font-medium text-sm">Telegram</Label>
                      <Switch
                        checked={Boolean(config?.platforms?.telegram?.enabled)}
                        onCheckedChange={(v: boolean) =>
                          patchConfig(
                            { platforms: { telegram: { enabled: v } } },
                            `Telegram bot ${v ? "enabled" : "disabled"}`,
                          )
                        }
                        data-testid="config-platform-telegram-toggle"
                      />
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <Label className="text-xs text-muted-foreground whitespace-nowrap">
                        Every
                      </Label>
                      <Input
                        type="number"
                        min="1"
                        max="48"
                        value={config?.platforms?.telegram?.post_frequency_hours ?? 6}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setConfig({
                            ...config,
                            platforms: {
                              ...config.platforms,
                              telegram: {
                                ...config.platforms.telegram,
                                post_frequency_hours: Number(e.target.value),
                              },
                            },
                          })
                        }
                        onBlur={(e: React.FocusEvent<HTMLInputElement>) =>
                          patchConfig(
                            {
                              platforms: {
                                telegram: {
                                  post_frequency_hours: Number(e.target.value),
                                },
                              },
                            },
                            "Telegram frequency saved",
                          )
                        }
                        className="w-20 h-8 font-mono text-sm"
                        data-testid="config-platform-telegram-frequency"
                      />
                      <Label className="text-xs text-muted-foreground">hours</Label>
                    </div>
                  </div>
                </div>
              </div>

              {/* Content modes + LLM */}
              <div className="rounded-xl border border-border bg-card p-5 space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles size={16} className="text-muted-foreground" />
                  <div className="font-display font-semibold">Content & LLM</div>
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    Enabled content types
                  </Label>
                  <div className="mt-3 space-y-2">
                    {["prophecy", "market_commentary", "vault_update", "kol_reply"].map(
                      (ct) => (
                        <div
                          key={ct}
                          className="flex items-center justify-between p-2 rounded-md border border-border/60 bg-background/40"
                        >
                          <span className="text-sm flex items-center gap-2">
                            <span className="text-base leading-none">
                              {CONTENT_TYPE_ICONS[ct] || "•"}
                            </span>
                            <span className="font-mono text-xs uppercase tracking-widest">
                              {ct.replace("_", " ")}
                            </span>
                          </span>
                          <Switch
                            checked={Boolean(config?.content_modes?.[ct])}
                            onCheckedChange={(v: boolean) =>
                              patchConfig(
                                { content_modes: { [ct]: v } },
                                `${ct} ${v ? "on" : "off"}`,
                              )
                            }
                            data-testid={`config-content-${ct}-toggle`}
                          />
                        </div>
                      ),
                    )}
                  </div>
                </div>

                <Separator />

                {/* ---- Sprint 18 — Prompt v2 toggle ---- */}
                <div className="rounded-md border border-border/60 bg-background/40 p-3 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <Label className="text-xs uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                      <Sparkles size={13} className="text-[#F59E0B]" />
                      Prompt V2 — 5 weighted templates
                    </Label>
                    <Switch
                      checked={Boolean(config?.prompt_v2?.enabled)}
                      onCheckedChange={(v: boolean) =>
                        patchConfig(
                          { prompt_v2: { enabled: v } },
                          `Prompt v2 ${v ? "ENABLED" : "disabled"}`,
                        )
                      }
                      data-testid="config-prompt-v2-toggle"
                    />
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    When ON, the Prophet rolls between <span className="font-mono">lore</span> · <span className="font-mono">satire_news</span>{" "}
                    · <span className="font-mono">stats</span> · <span className="font-mono">prophecy</span> · <span className="font-mono">meme_visual</span>{" "}
                    using weighted random (4·3·1·1·1). Use the Cadence tab to whitelist archetypes per slot. Use the Preview tab → "Use V2" to test.
                  </p>
                </div>

                <Separator />
                <div>
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    LLM preset
                  </Label>
                  <Select
                    value={currentLlmId}
                    onValueChange={(id: string) => {
                      const preset = LLM_PRESETS.find((p) => p.id === id);
                      if (preset) {
                        patchConfig(
                          { llm: { provider: preset.provider, model: preset.model } },
                          `Switched to ${preset.label}`,
                        );
                      }
                    }}
                  >
                    <SelectTrigger className="mt-2" data-testid="config-llm-select">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {LLM_PRESETS.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.label}
                        </SelectItem>
                      ))}
                      {currentLlmId === "custom" && (
                        <SelectItem value="custom">
                          Custom · {config?.llm?.provider}/{config?.llm?.model}
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                  <div className="mt-2 font-mono text-[10px] text-muted-foreground">
                    provider={config?.llm?.provider} · model={config?.llm?.model}
                  </div>
                </div>

                <Separator />

                {/* ============== CUSTOM LLM KEYS · BYO API ============== */}
                {/* Sprint 22.3 split — UI + dialog + handlers live in
                    <CustomLlmKeysSection />. We only pass the parent's
                    `config` snapshot + `loadConfig` callback. */}
                <CustomLlmKeysSection
                  api={API}
                  headers={headers}
                  config={config}
                  onConfigReload={loadConfig}
                />

                <Separator />

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                      Heartbeat (min)
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      max="1440"
                      value={config?.heartbeat_interval_minutes ?? 5}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setConfig({
                          ...config,
                          heartbeat_interval_minutes: Number(e.target.value),
                        })
                      }
                      onBlur={(e: React.FocusEvent<HTMLInputElement>) =>
                        patchConfig(
                          { heartbeat_interval_minutes: Number(e.target.value) },
                          "Heartbeat interval saved",
                        )
                      }
                      className="mt-2 font-mono"
                      data-testid="config-heartbeat-interval"
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                      Max posts / day
                    </Label>
                    <Input
                      type="number"
                      min="0"
                      max="500"
                      value={config?.max_posts_per_day ?? 12}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setConfig({
                          ...config,
                          max_posts_per_day: Number(e.target.value),
                        })
                      }
                      onBlur={(e: React.FocusEvent<HTMLInputElement>) =>
                        patchConfig(
                          { max_posts_per_day: Number(e.target.value) },
                          "Daily cap saved",
                        )
                      }
                      className="mt-2 font-mono"
                      data-testid="config-max-posts"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 items-center">
              <Button
                variant="outline"
                size="sm"
                onClick={manualHeartbeat}
                className="rounded-[var(--btn-radius)]"
                data-testid="config-manual-heartbeat"
              >
                <Activity size={14} className="mr-1" /> Ping heartbeat
              </Button>
              <div className="font-mono text-[11px] text-muted-foreground ml-2">
                last update:{" "}
                {config?.last_updated_at
                  ? new Date(config.last_updated_at).toLocaleString()
                  : "—"}{" "}
                by {config?.updated_by || "—"}
              </div>
            </div>

            {/* -------------------- NEWS FEED (extracted to TSX) -------------------- */}
            <Separator className="my-2" />
            <NewsFeedSection
              api={API}
              headers={headers}
              config={config}
              setConfig={setConfig}
              patchConfig={patchConfig}
            />

            {/* -------------------- LOYALTY ENGINE (extracted to TSX) -------------------- */}
            <Separator className="my-2" />
            <LoyaltySection api={API} headers={headers} />

            {/* -------------------- NEWS REPOST (extracted to TSX) -------------------- */}
            <Separator className="my-2" />
            <NewsRepostSection api={API} headers={headers} />
          </TabsContent>

          {/* -------------------- PREVIEW TAB -------------------- */}
          {/* -------------------- PREVIEW TAB -------------------- */}
          <TabsContent value="preview" className="mt-6">
            <AdminPreviewSection
              api={API}
              headers={headers}
              llmInfo={{ provider: config?.llm?.provider, model: config?.llm?.model }}
            />
          </TabsContent>

          {/* -------------------- CADENCE TAB -------------------- */}
          <TabsContent value="cadence" className="mt-6">
            <AdminCadenceSection api={API} headers={headers} />
          </TabsContent>

          {/* -------------------- JOBS TAB -------------------- */}
          {/* -------------------- JOBS TAB -------------------- */}
          <TabsContent value="jobs" className="mt-6">
            <AdminJobsSection api={API} headers={headers} />
          </TabsContent>

          {/* -------------------- LOGS TAB -------------------- */}
          {/* -------------------- LOGS TAB -------------------- */}
          <TabsContent value="logs" className="mt-6 space-y-4">
            <AdminLogsSection api={API} headers={headers} />
          </TabsContent>
        </Tabs>
      </main>

      {/* Custom LLM keys dialog has moved to <CustomLlmKeysSection />
          (Sprint 22.3 split). The child component owns the full flow —
          it renders the provider cards inline in the Config tab and the
          <Dialog> next to them via a React Fragment. */}
    </div>
  );
}
