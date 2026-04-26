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
  Rss,
  RefreshCw,
  Newspaper,
  ExternalLink,
  KeyRound,
  Eye,
  EyeOff,
  Trash2,
  Lock as LockIcon,
  ShieldCheck,
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { logger } from "@/lib/logger";
import LoyaltySection from "@/pages/admin/sections/LoyaltySection";
import NewsRepostSection from "@/pages/admin/sections/NewsRepostSection";

const API = process.env.REACT_APP_BACKEND_URL;

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
  const [token] = useState(() => getAdminToken());
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

  // ---- Manual Prophet inspiration ----
  // `previewKeywords` is a comma-separated string in the input; we split + trim
  // before sending so admins can type "powell, china tariffs, opec" naturally.
  const [previewKeywords, setPreviewKeywords] = useState("");
  const [useNewsContext, setUseNewsContext] = useState(false);

  // ---- News-feed aggregator state (Config tab "News Feed" section) ----
  const [news, setNews] = useState(null); // { items, last_refresh_at, last_refresh_stats }
  const [newsBusy, setNewsBusy] = useState(false);
  const [newsFeedsDraft, setNewsFeedsDraft] = useState("");
  const [newsKeywordsDraft, setNewsKeywordsDraft] = useState("");

  // Loyalty + News-repost have moved to dedicated TSX section components
  // (Sprint 5 split). They own their state and API calls — see
  // /pages/admin/sections/{LoyaltySection,NewsRepostSection}.tsx.

  // ---- Custom LLM keys vault (Config tab "Custom LLM keys" section) ----
  // The dialog is shared across the 3 providers — only one can be open at a time.
  const [llmSecretDialogOpen, setLlmSecretDialogOpen] = useState(false);
  const [llmSecretProvider, setLlmSecretProvider] = useState("openai");
  const [llmSecretInput, setLlmSecretInput] = useState("");
  const [llmSecretLabel, setLlmSecretLabel] = useState("");
  const [llmSecretReveal, setLlmSecretReveal] = useState(false);
  const [llmSecretBusy, setLlmSecretBusy] = useState(false);
  const [llmSecretError, setLlmSecretError] = useState(null);

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

  // Sync the news-feed text-area drafts with whatever is currently saved.
  // When `feeds` / `keywords` are empty in config, the backend treats them
  // as "use curated defaults" — we mirror that by pre-filling the input
  // with the defaults so admins always see *something* to work from.
  useEffect(() => {
    const nf = config?.news_feed;
    if (!nf) return;
    const feedsList =
      nf.feeds && nf.feeds.length > 0 ? nf.feeds : nf.default_feeds || [];
    const kwList =
      nf.keywords && nf.keywords.length > 0
        ? nf.keywords
        : nf.default_keywords || [];
    setNewsFeedsDraft(feedsList.join("\n"));
    setNewsKeywordsDraft(kwList.join(", "));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config?.news_feed?.feeds, config?.news_feed?.keywords]);

  async function bootstrap() {
    try {
      await Promise.all([
        loadConfig(),
        loadJobs(),
        loadPosts(),
        loadContentTypes(),
        loadNews(),
      ]);
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

  async function loadNews() {
    try {
      const { data } = await axios.get(`${API}/api/admin/bots/news`, { headers });
      setNews(data);
    } catch (err) {
      logger.error(err);
    }
  }

  async function refreshNewsNow() {
    setNewsBusy(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/bots/news/refresh`,
        {},
        { headers },
      );
      toast.success(
        `News refreshed — ${data.added} new / ${data.kept} kept / ${data.fetched} fetched`,
      );
      await loadNews();
      // Also re-pull the config so the "last refresh" pill updates
      await bootstrap();
    } catch (err) {
      logger.error(err);
      toast.error(err?.response?.data?.detail || "News refresh failed");
    } finally {
      setNewsBusy(false);
    }
  }

  function openLlmSecretDialog(provider) {
    setLlmSecretProvider(provider);
    setLlmSecretInput("");
    setLlmSecretLabel("");
    setLlmSecretReveal(false);
    setLlmSecretError(null);
    setLlmSecretDialogOpen(true);
  }

  async function submitLlmSecret() {
    setLlmSecretError(null);
    const key = (llmSecretInput || "").trim();
    if (key.length < 8) {
      setLlmSecretError("Key looks too short — paste the full key.");
      return;
    }
    setLlmSecretBusy(true);
    try {
      await axios.put(
        `${API}/api/admin/bots/llm-secrets`,
        {
          provider: llmSecretProvider,
          api_key: key,
          label: (llmSecretLabel || "").trim() || undefined,
        },
        { headers },
      );
      toast.success(`${llmSecretProvider.toUpperCase()} key saved (encrypted)`);
      setLlmSecretDialogOpen(false);
      setLlmSecretInput("");
      setLlmSecretLabel("");
      // Refetch config so the masked status updates instantly.
      await loadConfig();
    } catch (err) {
      logger.error(err);
      const msg = err?.response?.data?.detail || "Failed to save key";
      setLlmSecretError(msg);
      toast.error(msg);
    } finally {
      setLlmSecretBusy(false);
    }
  }

  async function revokeLlmSecret(provider) {
    if (
      !window.confirm(
        `Revoke the stored ${provider.toUpperCase()} key? The bot will fall back to the Emergent universal key on the next call.`,
      )
    ) {
      return;
    }
    try {
      await axios.delete(`${API}/api/admin/bots/llm-secrets/${provider}`, {
        headers,
      });
      toast.success(`${provider.toUpperCase()} key revoked`);
      await loadConfig();
    } catch (err) {
      logger.error(err);
      toast.error(err?.response?.data?.detail || "Revoke failed");
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
        use_news_context: useNewsContext,
      };
      if (previewType === "kol_reply") body.kol_post = kolPost.trim();
      const cleanedKw = (previewKeywords || "")
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean);
      if (cleanedKw.length) body.keywords = cleanedKw;

      const { data } = await axios.post(
        `${API}/api/admin/bots/generate-preview`,
        body,
        { headers },
      );
      setPreview(data);
      const sparkParts = [];
      if (cleanedKw.length) sparkParts.push(`${cleanedKw.length} keyword(s)`);
      if (useNewsContext) sparkParts.push("latest news");
      const spark = sparkParts.length ? ` (spark: ${sparkParts.join(" + ")})` : "";
      if (data.image_error) {
        toast.warning(`Image failed${spark}: ${data.image_error}`);
      } else if (data.image) {
        toast.success(`Prophet generated ${previewType} + Nano Banana${spark}`);
      } else {
        toast.success(`Prophet generated a ${previewType} preview${spark}`);
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

                {/* ============== CUSTOM LLM KEYS · BYO API ============== */}
                <div
                  className="rounded-xl border border-border bg-card p-5 space-y-3"
                  data-testid="custom-llm-keys-section"
                >
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-2">
                      <KeyRound size={16} className="text-[#F59E0B]" />
                      <div className="font-display font-semibold">
                        Custom LLM keys
                      </div>
                      <Badge
                        variant="outline"
                        className="font-mono text-[10px] uppercase tracking-widest"
                      >
                        BYO · encrypted
                      </Badge>
                    </div>
                    {config?.custom_llm_keys?._meta?.kek_configured ? (
                      <span className="font-mono text-[10px] uppercase tracking-widest text-[#18C964]">
                        ✓ vault armed
                      </span>
                    ) : (
                      <span className="font-mono text-[10px] uppercase tracking-widest text-[#E11D48]">
                        ⚠ KEK not configured (ephemeral)
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Bring your own OpenAI / Anthropic / Gemini API key. Keys
                    are encrypted at rest with AES-128-GCM (Fernet) using a
                    server-only KEK and never returned in plaintext. When
                    set, the bot uses your key directly for that provider —
                    no silent fallback to Emergent.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {["openai", "anthropic", "gemini"].map((prov) => {
                      const slot =
                        config?.custom_llm_keys?.[prov] || {};
                      const active = Boolean(slot.active);
                      return (
                        <div
                          key={prov}
                          className={`rounded-lg border p-3 flex flex-col gap-2 ${
                            active
                              ? "border-[#18C964]/40 bg-[#18C964]/5"
                              : "border-border bg-background/40"
                          }`}
                          data-testid={`custom-llm-card-${prov}`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                              {prov}
                            </span>
                            <span
                              className={`font-mono text-[9px] uppercase tracking-widest px-2 py-0.5 rounded-full border ${
                                active
                                  ? "border-[#18C964]/50 bg-[#18C964]/10 text-[#18C964]"
                                  : "border-border bg-muted text-muted-foreground"
                              }`}
                            >
                              {active ? "ACTIVE" : "NOT SET"}
                            </span>
                          </div>
                          <div className="font-mono text-xs text-foreground/85 truncate">
                            {active ? slot.mask || "***" : "—"}
                          </div>
                          {active && slot.label && (
                            <div className="text-[11px] text-muted-foreground truncate">
                              {slot.label}
                            </div>
                          )}
                          {active && (slot.set_at || slot.rotated_at) && (
                            <div className="font-mono text-[10px] text-muted-foreground">
                              rotated{" "}
                              {new Date(
                                slot.rotated_at || slot.set_at,
                              ).toLocaleDateString()}
                            </div>
                          )}
                          <div className="flex items-center gap-2 pt-1">
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              className="rounded-[var(--btn-radius)] flex-1"
                              onClick={() => openLlmSecretDialog(prov)}
                              data-testid={`custom-llm-set-${prov}`}
                            >
                              <KeyRound size={12} className="mr-1" />
                              {active ? "Rotate" : "Set key"}
                            </Button>
                            {active && (
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                className="rounded-[var(--btn-radius)] text-[#E11D48] hover:text-[#E11D48]/90 hover:bg-[#E11D48]/5"
                                onClick={() => revokeLlmSecret(prov)}
                                data-testid={`custom-llm-revoke-${prov}`}
                              >
                                <Trash2 size={12} />
                              </Button>
                            )}
                          </div>
                        </div>
                      );
                    })}
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

            {/* ============== NEWS FEED · GEOPOLITICS / MACRO ============== */}
            <Separator className="my-2" />
            <div
              className="rounded-xl border border-border bg-card p-5 space-y-4"
              data-testid="news-feed-section"
            >
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <Rss size={16} className="text-[#F59E0B]" />
                  <div className="font-display font-semibold">
                    News feed · geopolitics + macro
                  </div>
                  <Badge
                    variant="outline"
                    className="font-mono text-[10px] uppercase tracking-widest"
                  >
                    inspiration source
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-muted-foreground">
                    last refresh:{" "}
                    {config?.news_feed?.last_refresh_at
                      ? new Date(
                          config.news_feed.last_refresh_at,
                        ).toLocaleString()
                      : "—"}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={refreshNewsNow}
                    disabled={newsBusy}
                    className="rounded-[var(--btn-radius)]"
                    data-testid="news-feed-refresh-btn"
                  >
                    <RefreshCw
                      size={13}
                      className={`mr-1 ${newsBusy ? "animate-spin" : ""}`}
                    />
                    Refresh now
                  </Button>
                </div>
              </div>

              {config?.news_feed?.last_refresh_stats && (
                <div className="font-mono text-[11px] text-muted-foreground">
                  fetched={" "}
                  <span className="text-foreground/80">
                    {config.news_feed.last_refresh_stats.fetched ?? "?"}
                  </span>
                  {" · "}kept{" "}
                  <span className="text-foreground/80">
                    {config.news_feed.last_refresh_stats.kept ?? "?"}
                  </span>
                  {" · "}new{" "}
                  <span className="text-[#F59E0B]">
                    {config.news_feed.last_refresh_stats.added ?? "?"}
                  </span>
                  {" · "}feeds{" "}
                  <span className="text-foreground/80">
                    {config.news_feed.last_refresh_stats.feeds ?? "?"}
                  </span>
                </div>
              )}

              {/* Per-platform toggles */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {["x", "telegram"].map((plat) => (
                  <div
                    key={plat}
                    className="flex items-center justify-between rounded-lg border border-border bg-background/40 p-3"
                  >
                    <div>
                      <div className="font-display font-semibold capitalize">
                        {plat}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Inject latest headlines as Prophet inspiration
                      </div>
                    </div>
                    <Switch
                      checked={Boolean(
                        config?.news_feed?.enabled_for?.[plat],
                      )}
                      onCheckedChange={(checked) =>
                        patchConfig(
                          {
                            news_feed: {
                              enabled_for: {
                                ...(config?.news_feed?.enabled_for || {}),
                                [plat]: checked,
                              },
                            },
                          },
                          `News feed for ${plat} ${checked ? "enabled" : "disabled"}`,
                        )
                      }
                      data-testid={`news-feed-toggle-${plat}`}
                    />
                  </div>
                ))}
              </div>

              {/* Interval + headlines per post */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    Refresh interval (h)
                  </Label>
                  <Input
                    type="number"
                    min="1"
                    max="24"
                    value={config?.news_feed?.fetch_interval_hours ?? 6}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        news_feed: {
                          ...config.news_feed,
                          fetch_interval_hours: Number(e.target.value),
                        },
                      })
                    }
                    onBlur={(e) =>
                      patchConfig(
                        {
                          news_feed: {
                            fetch_interval_hours: Number(e.target.value),
                          },
                        },
                        "News refresh interval saved",
                      )
                    }
                    className="mt-2 font-mono"
                    data-testid="news-feed-interval"
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    Headlines per post
                  </Label>
                  <Input
                    type="number"
                    min="0"
                    max="10"
                    value={config?.news_feed?.headlines_per_post ?? 5}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        news_feed: {
                          ...config.news_feed,
                          headlines_per_post: Number(e.target.value),
                        },
                      })
                    }
                    onBlur={(e) =>
                      patchConfig(
                        {
                          news_feed: {
                            headlines_per_post: Number(e.target.value),
                          },
                        },
                        "Headlines per post saved",
                      )
                    }
                    className="mt-2 font-mono"
                    data-testid="news-feed-headlines"
                  />
                </div>
              </div>

              {/* RSS feeds editor */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    RSS feeds (one per line)
                  </Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
                    onClick={() => {
                      const defaults =
                        config?.news_feed?.default_feeds || [];
                      setNewsFeedsDraft(defaults.join("\n"));
                      patchConfig(
                        { news_feed: { feeds: [] } },
                        "Reset to default feeds",
                      );
                    }}
                    data-testid="news-feed-feeds-reset"
                  >
                    Reset to default
                  </Button>
                </div>
                <textarea
                  value={newsFeedsDraft}
                  onChange={(e) => setNewsFeedsDraft(e.target.value)}
                  onBlur={() =>
                    patchConfig(
                      {
                        news_feed: {
                          feeds: newsFeedsDraft
                            .split(/\r?\n/)
                            .map((s) => s.trim())
                            .filter(Boolean),
                        },
                      },
                      "RSS feeds saved",
                    )
                  }
                  rows={6}
                  className="w-full mt-1 rounded-md border border-border bg-background px-3 py-2 font-mono text-[11px] text-foreground/85 leading-relaxed focus:outline-none focus:ring-2 focus:ring-[#F59E0B]/40"
                  spellCheck={false}
                  placeholder="https://feeds.bbci.co.uk/news/world/rss.xml"
                  data-testid="news-feed-urls"
                />
              </div>

              {/* Keywords editor */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    Filter keywords (comma separated)
                  </Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
                    onClick={() => {
                      const defaults =
                        config?.news_feed?.default_keywords || [];
                      setNewsKeywordsDraft(defaults.join(", "));
                      patchConfig(
                        { news_feed: { keywords: [] } },
                        "Reset to default keywords",
                      );
                    }}
                    data-testid="news-feed-keywords-reset"
                  >
                    Reset to default
                  </Button>
                </div>
                <textarea
                  value={newsKeywordsDraft}
                  onChange={(e) => setNewsKeywordsDraft(e.target.value)}
                  onBlur={() =>
                    patchConfig(
                      {
                        news_feed: {
                          keywords: newsKeywordsDraft
                            .split(",")
                            .map((s) => s.trim())
                            .filter(Boolean),
                        },
                      },
                      "Keywords saved",
                    )
                  }
                  rows={3}
                  className="w-full mt-1 rounded-md border border-border bg-background px-3 py-2 font-mono text-[11px] text-foreground/85 leading-relaxed focus:outline-none focus:ring-2 focus:ring-[#F59E0B]/40"
                  spellCheck={false}
                  placeholder="war, ukraine, fed, ECB, inflation, ..."
                  data-testid="news-feed-keywords"
                />
              </div>

              {/* Headlines preview */}
              <div className="rounded-lg border border-border bg-background/40 p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Newspaper size={13} className="text-[#2DD4BF]" />
                    <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                      Latest kept headlines (top 5)
                    </div>
                  </div>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {news?.items?.length ?? 0} item(s) buffered
                  </span>
                </div>
                {news?.items && news.items.length > 0 ? (
                  <ul
                    className="space-y-1.5 text-xs leading-relaxed"
                    data-testid="news-feed-preview-list"
                  >
                    {news.items.slice(0, 5).map((it) => (
                      <li
                        key={it.id}
                        className="flex items-start gap-2"
                        data-testid={`news-feed-item-${it.id}`}
                      >
                        <span className="font-mono text-[10px] uppercase tracking-widest text-[#F59E0B] flex-none">
                          {(it.source || "?").slice(0, 18)}
                        </span>
                        <a
                          href={it.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-foreground/85 hover:underline inline-flex items-baseline gap-1 min-w-0"
                        >
                          <span className="truncate">{it.title}</span>
                          <ExternalLink
                            size={10}
                            className="flex-none text-muted-foreground"
                          />
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-xs text-muted-foreground italic">
                    No items yet — click "Refresh now" to fetch the feeds.
                  </div>
                )}
              </div>
            </div>

            {/* -------------------- LOYALTY ENGINE (extracted to TSX) -------------------- */}
            <Separator className="my-2" />
            <LoyaltySection api={API} headers={headers} />

            {/* -------------------- NEWS REPOST (extracted to TSX) -------------------- */}
            <Separator className="my-2" />
            <NewsRepostSection api={API} headers={headers} />
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

                {/* ============== INSPIRATION SOURCES ==============
                    Two manual ways for the admin to seed the Prophet:
                    1) `keywords` — a comma-separated list weaved into the post
                    2) `use_news_context` — inject the freshest geopolitics/macro
                       headlines (top 5) from the RSS aggregator. */}
                <div className="space-y-3 rounded-lg border border-border/60 bg-background/40 p-3">
                  <div className="flex items-center gap-2">
                    <Sparkles size={14} className="text-[#2DD4BF]" />
                    <Label className="font-medium text-sm">
                      Prophet inspiration
                    </Label>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                      Keywords (comma separated)
                    </Label>
                    <Input
                      value={previewKeywords}
                      onChange={(e) => setPreviewKeywords(e.target.value)}
                      placeholder="e.g. powell, tariffs, OPEC squeeze"
                      className="mt-2 font-mono text-xs"
                      data-testid="preview-keywords-input"
                    />
                    <p className="mt-1 text-[10.5px] text-muted-foreground leading-relaxed">
                      The Prophet weaves at least one of these into its
                      cynical commentary — without quoting them verbatim.
                    </p>
                  </div>
                  <div className="flex items-center justify-between gap-2 pt-1">
                    <div className="flex items-center gap-2">
                      <Newspaper size={14} className="text-[#F59E0B]" />
                      <Label className="text-sm">
                        Use latest news headlines
                      </Label>
                    </div>
                    <Switch
                      checked={useNewsContext}
                      onCheckedChange={setUseNewsContext}
                      data-testid="preview-news-toggle"
                    />
                  </div>
                  {useNewsContext && (
                    <p className="text-[10.5px] text-muted-foreground leading-relaxed">
                      Top 5 geopolitics/macro headlines from the RSS
                      aggregator are injected as inspiration. Configure
                      feeds + keywords in the Config tab.
                    </p>
                  )}
                </div>

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

      {/* Dialog: set / rotate a custom LLM API key */}
      <Dialog
        open={llmSecretDialogOpen}
        onOpenChange={(open) => {
          if (!llmSecretBusy) setLlmSecretDialogOpen(open);
        }}
      >
        <DialogContent
          className="sm:max-w-md"
          data-testid="custom-llm-dialog"
        >
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <LockIcon size={14} className="text-[#F59E0B]" />
              Set {llmSecretProvider.toUpperCase()} API key
            </DialogTitle>
            <DialogDescription>
              The key is encrypted at rest with AES-128-GCM and never
              returned by any GET endpoint. Only a masked fingerprint
              (e.g. <code>sk-...A1B2</code>) is shown in the UI after
              save.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <div>
              <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                API key
              </Label>
              <div className="relative mt-2">
                <Input
                  type={llmSecretReveal ? "text" : "password"}
                  value={llmSecretInput}
                  onChange={(e) => setLlmSecretInput(e.target.value)}
                  placeholder={
                    llmSecretProvider === "openai"
                      ? "sk-proj-..."
                      : llmSecretProvider === "anthropic"
                        ? "sk-ant-..."
                        : "AIzaSy..."
                  }
                  spellCheck={false}
                  autoComplete="off"
                  className="font-mono text-xs pr-10"
                  data-testid="custom-llm-key-input"
                />
                <button
                  type="button"
                  onClick={() => setLlmSecretReveal((v) => !v)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={
                    llmSecretReveal ? "Hide key" : "Reveal key"
                  }
                  data-testid="custom-llm-reveal-toggle"
                >
                  {llmSecretReveal ? (
                    <EyeOff size={14} />
                  ) : (
                    <Eye size={14} />
                  )}
                </button>
              </div>
              <p className="mt-1 text-[10.5px] text-muted-foreground leading-relaxed">
                Format check: must start with{" "}
                <code>
                  {llmSecretProvider === "openai"
                    ? "sk-"
                    : llmSecretProvider === "anthropic"
                      ? "sk-ant-"
                      : "AIza"}
                </code>
                . The server validates the shape before storing.
              </p>
            </div>

            <div>
              <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                Label (optional)
              </Label>
              <Input
                value={llmSecretLabel}
                onChange={(e) => setLlmSecretLabel(e.target.value)}
                placeholder={`e.g. "Personal ${llmSecretProvider} account"`}
                className="mt-2 font-mono text-xs"
                data-testid="custom-llm-label-input"
              />
            </div>

            {llmSecretError && (
              <div className="text-xs text-[#E11D48] font-mono leading-relaxed">
                {llmSecretError}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={llmSecretBusy}
              onClick={() => setLlmSecretDialogOpen(false)}
              className="rounded-[var(--btn-radius)]"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={submitLlmSecret}
              disabled={llmSecretBusy || llmSecretInput.length < 8}
              className="rounded-[var(--btn-radius)]"
              data-testid="custom-llm-submit"
            >
              {llmSecretBusy ? "Encrypting…" : "Save securely"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
