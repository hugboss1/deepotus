import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
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

const API = process.env.REACT_APP_BACKEND_URL;
const TOKEN_KEY = "deepotus_admin_token";

const CONTENT_TYPE_ICONS = {
  prophecy: "🔮",
  market_commentary: "📉",
  vault_update: "🔒",
  kol_reply: "🕶️",
};

const STATUS_COLOR = {
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

export default function AdminBots() {
  const navigate = useNavigate();
  const [token] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [config, setConfig] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [posts, setPosts] = useState(null);
  const [contentTypes, setContentTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  // Preview panel state
  const [previewType, setPreviewType] = useState("prophecy");
  const [previewPlatform, setPreviewPlatform] = useState("x");
  const [kolPost, setKolPost] = useState("");
  const [preview, setPreview] = useState(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [includeImage, setIncludeImage] = useState(false);
  const [imageAspect, setImageAspect] = useState("16:9");

  // Filters for post log
  const [platformFilter, setPlatformFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);

  useEffect(() => {
    if (!token) {
      navigate("/admin");
      return;
    }
    bootstrap();
    const id = setInterval(() => {
      loadJobs();
      loadPosts();
    }, 10000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadPosts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [platformFilter, statusFilter]);

  async function bootstrap() {
    try {
      await Promise.all([loadConfig(), loadJobs(), loadPosts(), loadContentTypes()]);
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
        localStorage.removeItem(TOKEN_KEY);
        navigate("/admin");
        return;
      }
      logger.error(err);
      toast.error("Could not load bot config");
    }
  }

  async function loadJobs() {
    try {
      const { data } = await axios.get(`${API}/api/admin/bots/jobs`, { headers });
      setJobs(Array.isArray(data) ? data : []);
    } catch (err) {
      logger.error(err);
    }
  }

  async function loadPosts() {
    try {
      const params = new URLSearchParams({ limit: "30", skip: "0" });
      if (platformFilter && platformFilter !== "all") params.set("platform", platformFilter);
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter);
      const { data } = await axios.get(`${API}/api/admin/bots/posts?${params.toString()}`, { headers });
      setPosts(data);
    } catch (err) {
      logger.error(err);
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

  async function patchConfig(patch, successMsg) {
    setBusy(true);
    try {
      const { data } = await axios.put(`${API}/api/admin/bots/config`, patch, { headers });
      setConfig(data);
      if (successMsg) toast.success(successMsg);
      loadJobs();
    } catch (err) {
      logger.error(err);
      toast.error(err?.response?.data?.detail || "Config update failed");
    } finally {
      setBusy(false);
    }
  }

  async function toggleKillSwitch(active) {
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
      loadJobs();
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
      loadPosts();
    } catch (err) {
      logger.error(err);
      toast.error("Heartbeat failed");
    }
  }

  async function generatePreview() {
    if (previewType === "kol_reply" && !kolPost.trim()) {
      toast.error("kol_post required for KOL reply");
      return;
    }
    setPreviewBusy(true);
    setPreview(null);
    try {
      const body = {
        content_type: previewType,
        platform: previewPlatform,
        include_image: includeImage,
        image_aspect_ratio: imageAspect,
      };
      if (previewType === "kol_reply") body.kol_post = kolPost.trim();
      const { data } = await axios.post(`${API}/api/admin/bots/generate-preview`, body, { headers });
      setPreview(data);
      if (data.image_error) {
        toast.warning(`Image failed: ${data.image_error}`);
      } else if (data.image) {
        toast.success(`Prophet generated ${previewType} + Nano Banana illustration`);
      } else {
        toast.success(`Prophet generated a ${previewType} preview`);
      }
    } catch (err) {
      logger.error(err);
      toast.error(err?.response?.data?.detail || "Generation failed");
    } finally {
      setPreviewBusy(false);
    }
  }

  function downloadPreviewImage() {
    if (!preview?.image?.image_base64) return;
    const { image_base64, mime_type, aspect_ratio, content_type } = preview.image;
    const a = document.createElement("a");
    a.href = `data:${mime_type};base64,${image_base64}`;
    const ext = mime_type?.includes("jpeg") ? "jpg" : "png";
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    a.download = `deepotus_${content_type}_${aspect_ratio.replace(":", "x")}_${ts}.${ext}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

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
  const statusCounts = posts?.status_counts || {};

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
                loadJobs();
                loadPosts();
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
                onClick={() => toggleKillSwitch(false)}
                disabled={!killOn || busy}
                className="rounded-[var(--btn-radius)] btn-press font-semibold"
                data-testid="admin-bots-kill-off"
              >
                <PlayCircle size={18} className="mr-2" /> Release
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
          <TabsList className="grid w-full grid-cols-4 max-w-xl">
            <TabsTrigger value="config" data-testid="tab-config">
              <Settings size={14} className="mr-1" /> Config
            </TabsTrigger>
            <TabsTrigger value="preview" data-testid="tab-preview">
              <Wand2 size={14} className="mr-1" /> Preview
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
                        onCheckedChange={(v) =>
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
                        onChange={(e) =>
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
                        onBlur={(e) =>
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
                        onCheckedChange={(v) =>
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
                        onChange={(e) =>
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
                        onBlur={(e) =>
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
                            onCheckedChange={(v) =>
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

                <div>
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    LLM preset
                  </Label>
                  <Select
                    value={currentLlmId}
                    onValueChange={(id) => {
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
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          heartbeat_interval_minutes: Number(e.target.value),
                        })
                      }
                      onBlur={(e) =>
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
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          max_posts_per_day: Number(e.target.value),
                        })
                      }
                      onBlur={(e) =>
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
          </TabsContent>

          {/* -------------------- PREVIEW TAB -------------------- */}
          <TabsContent value="preview" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
              <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 space-y-4">
                <div className="flex items-center gap-2">
                  <Wand2 size={16} className="text-[#2DD4BF]" />
                  <div className="font-display font-semibold">Studio input</div>
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    Content type
                  </Label>
                  <Select value={previewType} onValueChange={setPreviewType}>
                    <SelectTrigger className="mt-2" data-testid="preview-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {contentTypes.map((ct) => (
                        <SelectItem key={ct.id} value={ct.id}>
                          {CONTENT_TYPE_ICONS[ct.id] || "•"} {ct.label_en}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {contentTypes.find((c) => c.id === previewType) && (
                    <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                      {contentTypes.find((c) => c.id === previewType).description_en}
                    </p>
                  )}
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    Platform
                  </Label>
                  <Select value={previewPlatform} onValueChange={setPreviewPlatform}>
                    <SelectTrigger className="mt-2" data-testid="preview-platform-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="x">X · 270 chars</SelectItem>
                      <SelectItem value="telegram">Telegram · 800 chars</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {previewType === "kol_reply" && (
                  <div>
                    <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                      KOL tweet body
                    </Label>
                    <Textarea
                      rows={4}
                      placeholder="Paste the tweet the Prophet should reply to…"
                      value={kolPost}
                      onChange={(e) => setKolPost(e.target.value)}
                      className="mt-2 font-mono text-xs"
                      data-testid="preview-kol-input"
                    />
                  </div>
                )}

                <Separator />

                {/* Nano Banana image toggle */}
                <div className="space-y-3 rounded-lg border border-border/60 bg-background/40 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <ImageIcon size={14} className="text-[#F59E0B]" />
                      <Label className="font-medium text-sm">Nano Banana illustration</Label>
                    </div>
                    <Switch
                      checked={includeImage}
                      onCheckedChange={setIncludeImage}
                      data-testid="preview-image-toggle"
                    />
                  </div>
                  {includeImage && (
                    <div>
                      <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                        Aspect ratio
                      </Label>
                      <Select value={imageAspect} onValueChange={setImageAspect}>
                        <SelectTrigger className="mt-2" data-testid="preview-image-ratio">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="16:9">16:9 · X landscape</SelectItem>
                          <SelectItem value="3:4">3:4 · X portrait</SelectItem>
                          <SelectItem value="1:1">1:1 · Square</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="mt-2 text-[11px] text-muted-foreground leading-relaxed">
                        Uses Gemini Nano Banana via{" "}
                        <code className="font-mono text-[10px]">EMERGENT_IMAGE_LLM_KEY</code>{" "}
                        if set, else falls back to{" "}
                        <code className="font-mono text-[10px]">EMERGENT_LLM_KEY</code>.
                        Gen takes ~8–20s.
                      </p>
                    </div>
                  )}
                </div>

                <Button
                  onClick={generatePreview}
                  disabled={previewBusy}
                  className="w-full rounded-[var(--btn-radius)] btn-press font-semibold"
                  data-testid="preview-generate-button"
                >
                  {previewBusy ? (
                    <>
                      <RefreshCcw size={14} className="mr-2 animate-spin" />
                      {includeImage ? "Generating text + image…" : "Generating…"}
                    </>
                  ) : (
                    <>
                      <Sparkles size={14} className="mr-2" />
                      {includeImage ? "Generate text + illustration" : "Generate preview"}
                    </>
                  )}
                </Button>

                <div className="font-mono text-[10px] text-muted-foreground">
                  Preview uses LLM:{" "}
                  <span className="text-foreground/80">
                    {config?.llm?.provider}/{config?.llm?.model}
                  </span>
                </div>
              </div>

              <div className="lg:col-span-3 rounded-xl border border-border bg-card p-5 space-y-4 min-h-[320px]">
                <div className="flex items-center gap-2">
                  <Languages size={16} className="text-muted-foreground" />
                  <div className="font-display font-semibold">Prophet output</div>
                  {preview && (
                    <Badge
                      variant="outline"
                      className="ml-auto font-mono text-[10px] uppercase tracking-widest"
                      data-testid="preview-output-badge"
                    >
                      {preview.char_budget} chars · {preview.platform}
                    </Badge>
                  )}
                </div>

                {!preview && !previewBusy && (
                  <div className="flex flex-col items-center justify-center py-12 text-center gap-2 text-muted-foreground">
                    <Wand2 size={24} />
                    <div className="font-mono text-xs uppercase tracking-widest">
                      Awaiting generation
                    </div>
                    <div className="text-xs max-w-xs">
                      Pick a content type + platform on the left, then hit &quot;Generate
                      preview&quot;. Nothing is posted — pure dry-run.
                    </div>
                  </div>
                )}

                {preview && (
                  <div className="space-y-4">
                    <div className="rounded-lg border border-border/80 bg-background/40 p-4">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                        FR · {preview.content_fr.length}/{preview.char_budget}
                      </div>
                      <p
                        className="text-sm leading-relaxed whitespace-pre-wrap"
                        data-testid="preview-output-fr"
                      >
                        {preview.content_fr}
                      </p>
                    </div>
                    <div className="rounded-lg border border-border/80 bg-background/40 p-4">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                        EN · {preview.content_en.length}/{preview.char_budget}
                      </div>
                      <p
                        className="text-sm leading-relaxed whitespace-pre-wrap"
                        data-testid="preview-output-en"
                      >
                        {preview.content_en}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {preview.primary_emoji && (
                        <span className="text-2xl leading-none" aria-label="primary emoji">
                          {preview.primary_emoji}
                        </span>
                      )}
                      {(preview.hashtags || []).map((h) => (
                        <Badge
                          key={h}
                          variant="secondary"
                          className="font-mono text-[10px] uppercase tracking-widest"
                        >
                          #{h}
                        </Badge>
                      ))}
                    </div>

                    {/* Nano Banana illustration */}
                    {preview.image && (
                      <div
                        className="rounded-lg border border-border/80 bg-background/40 p-4 space-y-3"
                        data-testid="preview-output-image-block"
                      >
                        <div className="flex items-center justify-between flex-wrap gap-2">
                          <div className="flex items-center gap-2">
                            <ImageIcon size={14} className="text-[#F59E0B]" />
                            <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                              Illustration · {preview.image.aspect_ratio} · {Math.round((preview.image.size_bytes || 0) / 1024)} KB
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={downloadPreviewImage}
                            className="h-7 rounded-[var(--btn-radius)]"
                            data-testid="preview-output-image-download"
                          >
                            <Download size={12} className="mr-1" /> Download
                          </Button>
                        </div>
                        <div className="rounded-md overflow-hidden border border-border/60 bg-black">
                          <img
                            src={`data:${preview.image.mime_type};base64,${preview.image.image_base64}`}
                            alt="Prophet Studio illustration"
                            className="w-full h-auto block"
                            data-testid="preview-output-image"
                          />
                        </div>
                        <div className="font-mono text-[10px] text-muted-foreground">
                          via {preview.image.provider}/{preview.image.model}
                        </div>
                      </div>
                    )}

                    {preview.image_error && !preview.image && (
                      <div
                        className="rounded-md border border-[#E11D48]/40 bg-[#E11D48]/5 p-3 flex items-start gap-2"
                        data-testid="preview-output-image-error"
                      >
                        <AlertTriangle size={14} className="text-[#E11D48] shrink-0 mt-0.5" />
                        <div className="text-xs">
                          <div className="font-mono text-[10px] uppercase tracking-widest text-[#E11D48]">
                            Image generation failed
                          </div>
                          <div className="text-foreground/80 mt-1">{preview.image_error}</div>
                        </div>
                      </div>
                    )}

                    <div className="font-mono text-[10px] text-muted-foreground">
                      text via {preview.provider}/{preview.model}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>

          {/* -------------------- JOBS TAB -------------------- */}
          <TabsContent value="jobs" className="mt-6">
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center gap-2 mb-4">
                <Clock size={16} className="text-muted-foreground" />
                <div className="font-display font-semibold">Live scheduler jobs</div>
                <Badge
                  variant="outline"
                  className="ml-auto font-mono text-[10px] uppercase tracking-widest"
                >
                  {jobs.length} job{jobs.length > 1 ? "s" : ""}
                </Badge>
              </div>
              {jobs.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No jobs registered.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm font-mono">
                    <thead>
                      <tr className="text-left text-[10px] uppercase tracking-widest text-muted-foreground border-b border-border">
                        <th className="py-2 pr-4">ID</th>
                        <th className="py-2 pr-4">Trigger</th>
                        <th className="py-2 pr-4">Next run</th>
                        <th className="py-2 pr-4">Max inst</th>
                        <th className="py-2">Coalesce</th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobs.map((j) => (
                        <tr
                          key={j.id}
                          className="border-b border-border/50 hover:bg-background/40"
                          data-testid={`jobs-row-${j.id}`}
                        >
                          <td className="py-2 pr-4 text-foreground">{j.id}</td>
                          <td className="py-2 pr-4 text-foreground/70">{j.trigger}</td>
                          <td className="py-2 pr-4 text-foreground/70">
                            {j.next_run_time
                              ? new Date(j.next_run_time).toLocaleString()
                              : "—"}
                          </td>
                          <td className="py-2 pr-4 text-foreground/70">{j.max_instances}</td>
                          <td className="py-2 text-foreground/70">
                            {j.coalesce ? "yes" : "no"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </TabsContent>

          {/* -------------------- LOGS TAB -------------------- */}
          <TabsContent value="logs" className="mt-6 space-y-4">
            {/* Status histogram */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(statusCounts).map(([s, n]) => (
                <Badge
                  key={s}
                  variant="outline"
                  className="font-mono text-[10px] uppercase tracking-widest"
                  style={{
                    borderColor: `${STATUS_COLOR[s] || "#888"}66`,
                    color: STATUS_COLOR[s] || "#888",
                  }}
                  data-testid={`logs-count-${s}`}
                >
                  <TrendingUp size={10} className="mr-1" /> {s} · {n}
                </Badge>
              ))}
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <Label className="text-xs text-muted-foreground">Platform</Label>
                <Select value={platformFilter} onValueChange={setPlatformFilter}>
                  <SelectTrigger className="w-36 h-8" data-testid="logs-platform-filter">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="x">X</SelectItem>
                    <SelectItem value="telegram">Telegram</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-xs text-muted-foreground">Status</Label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-36 h-8" data-testid="logs-status-filter">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="heartbeat">Heartbeat</SelectItem>
                    <SelectItem value="posted">Posted</SelectItem>
                    <SelectItem value="killed">Killed</SelectItem>
                    <SelectItem value="skipped">Skipped</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Post log table */}
            <div className="rounded-xl border border-border bg-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-background/40">
                    <tr className="text-left text-[10px] uppercase tracking-widest text-muted-foreground">
                      <th className="py-2.5 px-4">When</th>
                      <th className="py-2.5 px-4">Platform</th>
                      <th className="py-2.5 px-4">Type</th>
                      <th className="py-2.5 px-4">Status</th>
                      <th className="py-2.5 px-4">Content / error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(posts?.items || []).length === 0 ? (
                      <tr>
                        <td
                          colSpan={5}
                          className="py-10 text-center text-muted-foreground font-mono text-xs"
                        >
                          No entries match the filters yet.
                        </td>
                      </tr>
                    ) : (
                      (posts?.items || []).map((p) => (
                        <tr
                          key={p.id}
                          className="border-t border-border/50 hover:bg-background/40"
                          data-testid={`logs-row-${p.id}`}
                        >
                          <td className="py-2 px-4 font-mono text-[11px] text-foreground/70 whitespace-nowrap">
                            {p.created_at
                              ? new Date(p.created_at).toLocaleTimeString()
                              : "—"}
                          </td>
                          <td className="py-2 px-4 font-mono text-xs text-foreground/80 uppercase tracking-widest">
                            {p.platform}
                          </td>
                          <td className="py-2 px-4 font-mono text-xs text-foreground/80">
                            {p.content_type}
                          </td>
                          <td className="py-2 px-4">
                            <span
                              className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full border"
                              style={{
                                borderColor: `${STATUS_COLOR[p.status] || "#888"}66`,
                                color: STATUS_COLOR[p.status] || "#888",
                              }}
                            >
                              {p.status}
                            </span>
                          </td>
                          <td className="py-2 px-4 text-xs text-foreground/75 max-w-sm truncate">
                            {p.error ? (
                              <span className="text-[#E11D48]">{p.error}</span>
                            ) : (
                              p.content || "—"
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="font-mono text-[10px] text-muted-foreground">
              showing {(posts?.items || []).length} of {posts?.total ?? 0} · auto-refresh
              every 10 s
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
