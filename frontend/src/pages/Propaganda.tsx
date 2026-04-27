/**
 * PROTOCOL ΔΣ — Propaganda Engine admin panel.
 *
 * Surface for the operator to:
 *   • flip the global Panic Kill Switch,
 *   • enable / disable triggers and tweak their policy + cooldown,
 *   • CRUD the message templates per trigger,
 *   • review the approval queue and approve / reject pending messages,
 *   • inspect the audit feed.
 *
 * Auth: every API call rides the admin JWT stored in sessionStorage. The
 * panic switch and approve / reject actions require 2FA on the backend —
 * the UI surfaces the resulting 403 with a clear toast pointing the user
 * to /admin/security.
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Flame,
  ListChecks,
  Loader2,
  MessageSquareText,
  Pencil,
  Plus,
  Power,
  Settings as SettingsIcon,
  ShieldOff,
  Trash2,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

import { getAdminToken } from "@/lib/adminAuth";
import { logger } from "@/lib/logger";

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------
const API: string = process.env.REACT_APP_BACKEND_URL || "";

interface Trigger {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
  policy: "auto" | "approval";
  cooldown_minutes: number;
  last_fired_at: string | null;
  fire_count: number;
  metadata: Record<string, unknown>;
}

interface Template {
  id: string;
  trigger_key: string;
  language: "en" | "fr";
  content: string;
  weight: number;
  mentions_vault: boolean;
  enabled: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

interface QueueItem {
  id: string;
  trigger_key: string;
  template_id: string | null;
  rendered_content: string;
  platforms: string[];
  payload: Record<string, unknown>;
  status:
    | "proposed"
    | "approved"
    | "sent"
    | "failed"
    | "rejected"
    | "killed";
  manual: boolean;
  proposed_at: string;
  approved_at: string | null;
  scheduled_for: string | null;
  sent_at: string | null;
  error: string | null;
  reject_reason: string | null;
}

interface ActivityEvent {
  id: string;
  type: string;
  trigger_key: string | null;
  queue_item_id: string | null;
  by_jti: string | null;
  ip: string | null;
  at: string;
  meta: Record<string, unknown>;
}

interface Settings {
  panic: boolean;
  default_locale: string;
  vault_link_every: number;
  vault_mention_counter: number;
  rate_limits: { per_hour: number; per_day: number; per_trigger_minutes: number };
  default_delay_seconds_min: number;
  default_delay_seconds_max: number;
  platforms: string[];
}

// ---------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------
function authHeaders() {
  const t = getAdminToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

function handleError(err: unknown, fallback: string) {
  // eslint-disable-next-line
  const detail = (err as any)?.response?.data?.detail;
  // eslint-disable-next-line
  const status = (err as any)?.response?.status;
  if (status === 403 && detail?.code === "TWOFA_REQUIRED") {
    toast.error("2FA required for this action", {
      description: "Enable 2FA from Admin → Security first.",
    });
    return;
  }
  toast.error(typeof detail === "string" ? detail : fallback);
  logger.error(err);
}

// ---------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------
export default function Propaganda() {
  const navigate = useNavigate();
  const token = getAdminToken();

  const [settings, setSettings] = useState<Settings | null>(null);
  const [tab, setTab] = useState<string>("triggers");
  const [busyPanic, setBusyPanic] = useState<boolean>(false);

  const loadSettings = useCallback(async () => {
    try {
      const { data } = await axios.get<Settings>(
        `${API}/api/admin/propaganda/settings`,
        { headers: authHeaders() },
      );
      setSettings(data);
    } catch (err) {
      handleError(err, "Failed to load settings");
    }
  }, []);

  useEffect(() => {
    if (!token) {
      navigate("/admin");
      return;
    }
    void loadSettings();
  }, [token, navigate, loadSettings]);

  const togglePanic = async (next: boolean) => {
    setBusyPanic(true);
    try {
      const { data } = await axios.post<Settings>(
        `${API}/api/admin/propaganda/panic`,
        { panic: next },
        { headers: authHeaders() },
      );
      setSettings(data);
      toast.success(
        next ? "Panic ON — pending messages killed." : "Panic OFF — engine resumed.",
      );
    } catch (err) {
      handleError(err, "Failed to toggle panic");
    } finally {
      setBusyPanic(false);
    }
  };

  if (!settings) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
        <Loader2 className="animate-spin" size={28} />
      </div>
    );
  }

  return (
    <div
      className="min-h-screen bg-background text-foreground p-6 md:p-10"
      data-testid="propaganda-page"
    >
      <header className="max-w-6xl mx-auto mb-8">
        <button
          type="button"
          onClick={() => navigate("/admin")}
          className="text-xs uppercase tracking-[0.3em] text-muted-foreground hover:text-foreground inline-flex items-center gap-2 mb-4"
          data-testid="propaganda-back"
        >
          <ArrowLeft size={14} /> Back to dashboard
        </button>

        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <div className="text-[10px] tracking-[0.4em] text-muted-foreground uppercase">
              $DEEPOTUS / PROTOCOL ΔΣ
            </div>
            <h1 className="text-2xl md:text-3xl font-medium mt-1">
              Propaganda Engine
            </h1>
            <p className="text-sm text-muted-foreground mt-1 max-w-xl">
              Scenario-based messaging fleet. Trigger detectors fire into an
              approval queue; the dispatcher posts to X + Telegram with a
              humanized 10–30 s delay.
            </p>
          </div>

          <PanicCard
            panic={settings.panic}
            busy={busyPanic}
            onToggle={togglePanic}
          />
        </div>
      </header>

      <main className="max-w-6xl mx-auto">
        <Tabs value={tab} onValueChange={setTab} className="w-full">
          <TabsList className="grid grid-cols-4 w-full md:w-auto">
            <TabsTrigger value="triggers" data-testid="propaganda-tab-triggers">
              <Flame size={14} className="mr-2" /> Triggers
            </TabsTrigger>
            <TabsTrigger value="templates" data-testid="propaganda-tab-templates">
              <MessageSquareText size={14} className="mr-2" /> Templates
            </TabsTrigger>
            <TabsTrigger value="queue" data-testid="propaganda-tab-queue">
              <ListChecks size={14} className="mr-2" /> Queue
            </TabsTrigger>
            <TabsTrigger value="activity" data-testid="propaganda-tab-activity">
              <Activity size={14} className="mr-2" /> Activity
            </TabsTrigger>
          </TabsList>

          <TabsContent value="triggers" className="mt-6">
            <TriggersTab />
          </TabsContent>
          <TabsContent value="templates" className="mt-6">
            <TemplatesTab />
          </TabsContent>
          <TabsContent value="queue" className="mt-6">
            <QueueTab />
          </TabsContent>
          <TabsContent value="activity" className="mt-6">
            <ActivityTab />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------
// Panic kill switch card
// ---------------------------------------------------------------------
interface PanicCardProps {
  panic: boolean;
  busy: boolean;
  onToggle: (next: boolean) => void;
}

function PanicCard({ panic, busy, onToggle }: PanicCardProps) {
  return (
    <div
      className={`rounded-md border p-4 min-w-[280px] ${
        panic
          ? "border-[#FF4D4D] bg-[#FF4D4D]/10"
          : "border-border bg-background/50"
      }`}
      data-testid="propaganda-panic-card"
    >
      <div className="flex items-center gap-2 text-[10px] tracking-[0.3em] uppercase text-muted-foreground">
        <ShieldOff size={12} /> Panic kill-switch
      </div>
      <div className="mt-2 flex items-center justify-between gap-4">
        <div>
          <div
            className={`text-sm font-mono ${
              panic ? "text-[#FF4D4D]" : "text-foreground/80"
            }`}
            data-testid="propaganda-panic-status"
          >
            {panic ? "ENGINE FROZEN" : "ENGINE LIVE"}
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5 max-w-[220px]">
            {panic
              ? "All pending dispatches were killed. New triggers are ignored."
              : "Triggers reach the queue. Auto-policy items will be sent."}
          </p>
        </div>
        <Button
          variant={panic ? "outline" : "destructive"}
          onClick={() => onToggle(!panic)}
          disabled={busy}
          className="rounded-[var(--btn-radius)] min-w-[110px]"
          data-testid="propaganda-panic-toggle"
        >
          {busy ? <Loader2 size={14} className="animate-spin" /> : (
            <>
              <Power size={14} className="mr-1.5" /> {panic ? "Resume" : "Panic"}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------
// Triggers tab
// ---------------------------------------------------------------------
function TriggersTab() {
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [fireOpen, setFireOpen] = useState<Trigger | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<{ items: Trigger[] }>(
        `${API}/api/admin/propaganda/triggers`,
        { headers: authHeaders() },
      );
      setTriggers(data.items);
    } catch (err) {
      handleError(err, "Failed to load triggers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const patch = async (key: string, body: Partial<Trigger>) => {
    try {
      await axios.patch(
        `${API}/api/admin/propaganda/triggers/${key}`,
        body,
        { headers: authHeaders() },
      );
      await load();
    } catch (err) {
      handleError(err, "Failed to update trigger");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="animate-spin" size={20} />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {triggers.map((t) => (
        <div
          key={t.key}
          className="rounded-md border border-border bg-background/40 p-4"
          data-testid={`trigger-row-${t.key}`}
        >
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-sm font-medium">{t.label}</h3>
                <Badge variant={t.enabled ? "default" : "secondary"}>
                  {t.enabled ? "ENABLED" : "DISABLED"}
                </Badge>
                <Badge variant="outline">policy: {t.policy}</Badge>
                <Badge variant="outline">
                  cooldown: {t.cooldown_minutes}m
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{t.description}</p>
              <div className="text-[11px] text-muted-foreground mt-2 font-mono">
                fired {t.fire_count}× ·{" "}
                {t.last_fired_at
                  ? `last ${new Date(t.last_fired_at).toLocaleString()}`
                  : "never fired"}
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-2 text-xs">
                <Switch
                  checked={t.enabled}
                  onCheckedChange={(v: boolean) => patch(t.key, { enabled: v })}
                  data-testid={`trigger-toggle-${t.key}`}
                />
                <span className="text-muted-foreground">on/off</span>
              </div>
              <Select
                value={t.policy}
                onValueChange={(v: string) =>
                  patch(t.key, { policy: v as "auto" | "approval" })
                }
              >
                <SelectTrigger
                  className="h-8 w-[130px] text-xs"
                  data-testid={`trigger-policy-${t.key}`}
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">auto-send</SelectItem>
                  <SelectItem value="approval">approval queue</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="default"
                size="sm"
                onClick={() => setFireOpen(t)}
                className="rounded-[var(--btn-radius)]"
                data-testid={`trigger-fire-${t.key}`}
              >
                <Flame size={13} className="mr-1" /> Fire now
              </Button>
            </div>
          </div>
        </div>
      ))}

      {fireOpen && (
        <FireDialog
          trigger={fireOpen}
          onClose={() => setFireOpen(null)}
          onFired={() => {
            setFireOpen(null);
            void load();
            toast.success("Trigger fired — check Queue tab.");
          }}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------
// Manual fire dialog
// ---------------------------------------------------------------------
interface FireDialogProps {
  trigger: Trigger;
  onClose: () => void;
  onFired: () => void;
}

function FireDialog({ trigger, onClose, onFired }: FireDialogProps) {
  const [busy, setBusy] = useState<boolean>(false);
  const [buyLink, setBuyLink] = useState<string>("");
  const [mcTier, setMcTier] = useState<number>(25_000);
  const [whaleAmount, setWhaleAmount] = useState<number>(7);
  const [raydiumLink, setRaydiumLink] = useState<string>("");

  const submit = async () => {
    setBusy(true);
    try {
      const payload_override: Record<string, unknown> = {};
      if (trigger.key === "mint" && buyLink) payload_override.buy_link = buyLink;
      if (trigger.key === "mc_milestone") {
        payload_override.mc_tier = mcTier;
        if (buyLink) payload_override.buy_link = buyLink;
      }
      if (trigger.key === "whale_buy") payload_override.whale_amount = whaleAmount;
      if (trigger.key === "raydium_migration" && raydiumLink) {
        payload_override.raydium_link = raydiumLink;
      }
      await axios.post(
        `${API}/api/admin/propaganda/fire`,
        { trigger_key: trigger.key, payload_override },
        { headers: authHeaders() },
      );
      onFired();
    } catch (err) {
      handleError(err, "Failed to fire trigger");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={(v: boolean) => !v && onClose()}>
      <DialogContent
        className="max-w-md"
        data-testid={`trigger-fire-dialog-${trigger.key}`}
      >
        <DialogHeader>
          <DialogTitle>Manual fire — {trigger.label}</DialogTitle>
          <DialogDescription>
            The detector runs in <strong>manual mode</strong> and pushes the
            chosen template into the queue (
            {trigger.policy === "auto"
              ? "auto-send: scheduled directly"
              : "approval queue: waits for 2FA-locked approve"}
            ).
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          {(trigger.key === "mint" || trigger.key === "mc_milestone") && (
            <div>
              <Label className="text-xs uppercase tracking-widest">
                Buy link (optional)
              </Label>
              <Input
                value={buyLink}
                onChange={(e) => setBuyLink(e.target.value)}
                placeholder="https://pump.fun/<mint>"
                className="font-mono text-xs"
                data-testid="trigger-fire-buy-link"
              />
            </div>
          )}
          {trigger.key === "mc_milestone" && (
            <div>
              <Label className="text-xs uppercase tracking-widest">
                Milestone tier (USD)
              </Label>
              <Input
                type="number"
                value={mcTier}
                min={1000}
                step={5000}
                onChange={(e) => setMcTier(Number(e.target.value || 0))}
                className="font-mono"
                data-testid="trigger-fire-mc-tier"
              />
            </div>
          )}
          {trigger.key === "whale_buy" && (
            <div>
              <Label className="text-xs uppercase tracking-widest">
                Whale buy amount (SOL)
              </Label>
              <Input
                type="number"
                value={whaleAmount}
                min={1}
                step={0.5}
                onChange={(e) => setWhaleAmount(Number(e.target.value || 0))}
                className="font-mono"
                data-testid="trigger-fire-whale-amount"
              />
            </div>
          )}
          {trigger.key === "raydium_migration" && (
            <div>
              <Label className="text-xs uppercase tracking-widest">
                Raydium link
              </Label>
              <Input
                value={raydiumLink}
                onChange={(e) => setRaydiumLink(e.target.value)}
                placeholder="https://raydium.io/swap/?inputCurrency=..."
                className="font-mono text-xs"
                data-testid="trigger-fire-raydium-link"
              />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={busy}
            className="rounded-[var(--btn-radius)]"
          >
            Cancel
          </Button>
          <Button
            onClick={submit}
            disabled={busy}
            className="rounded-[var(--btn-radius)]"
            data-testid="trigger-fire-submit"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : (
              <>
                <Flame size={14} className="mr-1" /> Fire
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------
// Templates tab
// ---------------------------------------------------------------------
function TemplatesTab() {
  const [items, setItems] = useState<Template[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterTrigger, setFilterTrigger] = useState<string>("all");
  const [filterLang, setFilterLang] = useState<string>("all");
  const [editing, setEditing] = useState<Template | "new" | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filterTrigger !== "all") params.trigger_key = filterTrigger;
      if (filterLang !== "all") params.language = filterLang;
      const { data } = await axios.get<{ items: Template[] }>(
        `${API}/api/admin/propaganda/templates`,
        { headers: authHeaders(), params },
      );
      setItems(data.items);
    } catch (err) {
      handleError(err, "Failed to load templates");
    } finally {
      setLoading(false);
    }
  }, [filterTrigger, filterLang]);

  useEffect(() => {
    void load();
  }, [load]);

  const remove = async (id: string) => {
    if (!window.confirm("Delete this template?")) return;
    try {
      await axios.delete(
        `${API}/api/admin/propaganda/templates/${id}`,
        { headers: authHeaders() },
      );
      toast.success("Template deleted");
      await load();
    } catch (err) {
      handleError(err, "Failed to delete template");
    }
  };

  const toggle = async (t: Template) => {
    try {
      await axios.patch(
        `${API}/api/admin/propaganda/templates/${t.id}`,
        { enabled: !t.enabled },
        { headers: authHeaders() },
      );
      await load();
    } catch (err) {
      handleError(err, "Failed to toggle template");
    }
  };

  const triggerKeys = useMemo(
    () => ["mint", "mc_milestone", "jeet_dip", "whale_buy", "raydium_migration"],
    [],
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <Select value={filterTrigger} onValueChange={setFilterTrigger}>
            <SelectTrigger className="h-9 w-[180px] text-xs">
              <SelectValue placeholder="Filter by trigger" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All triggers</SelectItem>
              {triggerKeys.map((k) => (
                <SelectItem key={k} value={k}>
                  {k}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterLang} onValueChange={setFilterLang}>
            <SelectTrigger className="h-9 w-[140px] text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All languages</SelectItem>
              <SelectItem value="en">EN</SelectItem>
              <SelectItem value="fr">FR</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button
          onClick={() => setEditing("new")}
          className="rounded-[var(--btn-radius)]"
          data-testid="template-new"
        >
          <Plus size={14} className="mr-1" /> New template
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin" size={20} />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center text-sm text-muted-foreground py-12">
          No templates match these filters.
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((t) => (
            <div
              key={t.id}
              className="rounded-md border border-border bg-background/40 p-3"
              data-testid={`template-row-${t.id}`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <Badge variant="outline" className="font-mono">
                      {t.trigger_key}
                    </Badge>
                    <Badge variant="outline" className="font-mono">
                      {t.language.toUpperCase()}
                    </Badge>
                    {t.mentions_vault && (
                      <Badge className="bg-[#F59E0B] text-black">vault-mention</Badge>
                    )}
                    {!t.enabled && <Badge variant="secondary">disabled</Badge>}
                    <span className="text-[10px] text-muted-foreground">
                      weight {t.weight} · v{t.version}
                    </span>
                  </div>
                  <p className="text-sm font-mono text-foreground/90 break-words">
                    {t.content}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => toggle(t)}
                    title={t.enabled ? "Disable" : "Enable"}
                    data-testid={`template-toggle-${t.id}`}
                  >
                    <Power size={14} />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => setEditing(t)}
                    data-testid={`template-edit-${t.id}`}
                  >
                    <Pencil size={14} />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => remove(t.id)}
                    data-testid={`template-delete-${t.id}`}
                  >
                    <Trash2 size={14} className="text-[#FF4D4D]" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {editing && (
        <TemplateEditor
          template={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={async () => {
            setEditing(null);
            await load();
          }}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------
// Template editor dialog
// ---------------------------------------------------------------------
interface TemplateEditorProps {
  template: Template | null;
  onClose: () => void;
  onSaved: () => void;
}

function TemplateEditor({ template, onClose, onSaved }: TemplateEditorProps) {
  const [busy, setBusy] = useState<boolean>(false);
  const [triggerKey, setTriggerKey] = useState<string>(
    template?.trigger_key || "mint",
  );
  const [language, setLanguage] = useState<"en" | "fr">(
    template?.language || "en",
  );
  const [content, setContent] = useState<string>(template?.content || "");
  const [weight, setWeight] = useState<number>(template?.weight || 1.0);
  const [mentionsVault, setMentionsVault] = useState<boolean>(
    template?.mentions_vault || false,
  );
  const [enabled, setEnabled] = useState<boolean>(template?.enabled ?? true);

  const submit = async () => {
    if (content.trim().length === 0) {
      toast.error("Content cannot be empty");
      return;
    }
    setBusy(true);
    try {
      if (template) {
        await axios.patch(
          `${API}/api/admin/propaganda/templates/${template.id}`,
          { content, language, weight, mentions_vault: mentionsVault, enabled },
          { headers: authHeaders() },
        );
        toast.success("Template updated");
      } else {
        await axios.post(
          `${API}/api/admin/propaganda/templates`,
          {
            trigger_key: triggerKey,
            language,
            content,
            weight,
            mentions_vault: mentionsVault,
            enabled,
          },
          { headers: authHeaders() },
        );
        toast.success("Template created");
      }
      onSaved();
    } catch (err) {
      handleError(err, "Failed to save template");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={(v: boolean) => !v && onClose()}>
      <DialogContent className="max-w-lg" data-testid="template-editor">
        <DialogHeader>
          <DialogTitle>
            {template ? "Edit template" : "New template"}
          </DialogTitle>
          <DialogDescription>
            Use placeholders like <code className="px-1 bg-muted rounded">{"{buy_link}"}</code>,{" "}
            <code className="px-1 bg-muted rounded">{"{mc_label}"}</code>,{" "}
            <code className="px-1 bg-muted rounded">{"{whale_amount}"}</code>{" "}
            — they're auto-filled at fire time.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          {!template && (
            <div>
              <Label className="text-xs uppercase tracking-widest">Trigger</Label>
              <Select value={triggerKey} onValueChange={setTriggerKey}>
                <SelectTrigger className="font-mono" data-testid="template-trigger-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mint">mint</SelectItem>
                  <SelectItem value="mc_milestone">mc_milestone</SelectItem>
                  <SelectItem value="jeet_dip">jeet_dip</SelectItem>
                  <SelectItem value="whale_buy">whale_buy</SelectItem>
                  <SelectItem value="raydium_migration">raydium_migration</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          <div>
            <Label className="text-xs uppercase tracking-widest">Language</Label>
            <Select
              value={language}
              onValueChange={(v: string) => setLanguage(v as "en" | "fr")}
            >
              <SelectTrigger className="font-mono" data-testid="template-language-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="fr">Français</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-xs uppercase tracking-widest">Content</Label>
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={5}
              className="font-mono text-sm"
              maxLength={1000}
              data-testid="template-content-input"
            />
            <div className="text-[10px] text-muted-foreground text-right mt-1">
              {content.length}/1000
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs uppercase tracking-widest">Weight</Label>
              <Input
                type="number"
                value={weight}
                step={0.1}
                min={0.1}
                max={5}
                onChange={(e) => setWeight(Number(e.target.value))}
                className="font-mono"
                data-testid="template-weight-input"
              />
            </div>
            <div className="flex items-end gap-4">
              <label className="flex items-center gap-2 cursor-pointer text-xs">
                <Switch
                  checked={mentionsVault}
                  onCheckedChange={setMentionsVault}
                  data-testid="template-mentions-vault"
                />
                <span>vault-mention</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-xs">
                <Switch
                  checked={enabled}
                  onCheckedChange={setEnabled}
                  data-testid="template-enabled"
                />
                <span>enabled</span>
              </label>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={busy}
            className="rounded-[var(--btn-radius)]"
          >
            Cancel
          </Button>
          <Button
            onClick={submit}
            disabled={busy}
            className="rounded-[var(--btn-radius)]"
            data-testid="template-save"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------
// Queue tab
// ---------------------------------------------------------------------
function QueueTab() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<{ items: QueueItem[] }>(
        `${API}/api/admin/propaganda/queue`,
        {
          headers: authHeaders(),
          params: statusFilter !== "all" ? { statuses: statusFilter } : {},
        },
      );
      setItems(data.items);
    } catch (err) {
      handleError(err, "Failed to load queue");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void load();
    const id = setInterval(load, 6000); // gentle polling
    return () => clearInterval(id);
  }, [load]);

  const approve = async (id: string) => {
    try {
      await axios.post(
        `${API}/api/admin/propaganda/queue/${id}/approve`,
        {},
        { headers: authHeaders() },
      );
      toast.success("Approved — message scheduled.");
      await load();
    } catch (err) {
      handleError(err, "Failed to approve");
    }
  };

  const reject = async (id: string) => {
    const reason = window.prompt("Reject reason (optional):") || "";
    try {
      await axios.post(
        `${API}/api/admin/propaganda/queue/${id}/reject`,
        { reason },
        { headers: authHeaders() },
      );
      toast.success("Rejected.");
      await load();
    } catch (err) {
      handleError(err, "Failed to reject");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="h-9 w-[180px] text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="proposed">Proposed</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="sent">Sent</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="killed">Killed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin" size={20} />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center text-sm text-muted-foreground py-12">
          Queue is empty.
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((q) => (
            <QueueRow
              key={q.id}
              item={q}
              onApprove={() => approve(q.id)}
              onReject={() => reject(q.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface QueueRowProps {
  item: QueueItem;
  onApprove: () => void;
  onReject: () => void;
}

function QueueRow({ item, onApprove, onReject }: QueueRowProps) {
  const statusColor: Record<string, string> = {
    proposed: "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30",
    approved: "bg-[#0EA5E9]/15 text-[#0EA5E9] border-[#0EA5E9]/30",
    sent: "bg-[#18C964]/15 text-[#18C964] border-[#18C964]/30",
    rejected: "bg-muted text-muted-foreground border-border",
    killed: "bg-[#FF4D4D]/15 text-[#FF4D4D] border-[#FF4D4D]/30",
    failed: "bg-[#FF4D4D]/15 text-[#FF4D4D] border-[#FF4D4D]/30",
  };
  return (
    <div
      className="rounded-md border border-border bg-background/40 p-3"
      data-testid={`queue-row-${item.id}`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <Badge variant="outline" className="font-mono">
              {item.trigger_key}
            </Badge>
            <span
              className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-widest border ${
                statusColor[item.status] || ""
              }`}
            >
              {item.status}
            </span>
            {item.manual && <Badge variant="secondary">manual</Badge>}
            <span className="text-[10px] text-muted-foreground">
              <Clock size={10} className="inline mr-1" />
              {new Date(item.proposed_at).toLocaleString()}
            </span>
          </div>
          <p className="text-sm font-mono text-foreground/90 break-words">
            {item.rendered_content}
          </p>
          <div className="text-[10px] text-muted-foreground mt-1 font-mono">
            platforms: {item.platforms.join(", ") || "—"} ·
            scheduled:{" "}
            {item.scheduled_for
              ? new Date(item.scheduled_for).toLocaleString()
              : "—"}
          </div>
          {item.error && (
            <div className="mt-1 text-[11px] text-[#FF4D4D] font-mono">
              error: {item.error}
            </div>
          )}
          {item.reject_reason && (
            <div className="mt-1 text-[11px] text-muted-foreground font-mono">
              rejected: {item.reject_reason}
            </div>
          )}
        </div>
        {item.status === "proposed" && (
          <div className="flex items-center gap-1 shrink-0">
            <Button
              size="sm"
              onClick={onApprove}
              className="rounded-[var(--btn-radius)]"
              data-testid={`queue-approve-${item.id}`}
            >
              <CheckCircle2 size={14} className="mr-1" /> Approve
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onReject}
              className="rounded-[var(--btn-radius)]"
              data-testid={`queue-reject-${item.id}`}
            >
              <X size={14} className="mr-1" /> Reject
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------
// Activity tab
// ---------------------------------------------------------------------
function ActivityTab() {
  const [items, setItems] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<{ items: ActivityEvent[] }>(
        `${API}/api/admin/propaganda/activity`,
        { headers: authHeaders(), params: { limit: 100 } },
      );
      setItems(data.items);
    } catch (err) {
      handleError(err, "Failed to load activity");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const colorByType: Record<string, string> = {
    fire: "text-[#0EA5E9]",
    fire_skip: "text-muted-foreground",
    fire_skip_disabled: "text-muted-foreground",
    fire_skip_panic: "text-[#FF4D4D]",
    fire_no_template: "text-[#F59E0B]",
    approve: "text-[#18C964]",
    reject: "text-[#F59E0B]",
    panic_on: "text-[#FF4D4D]",
    panic_off: "text-[#18C964]",
  };

  return (
    <div>
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin" size={20} />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center text-sm text-muted-foreground py-12">
          No activity recorded yet.
        </div>
      ) : (
        <ScrollArea className="h-[480px] pr-2">
          <ul className="space-y-1.5 font-mono text-[12px]">
            {items.map((e) => (
              <li
                key={e.id}
                className="flex items-start gap-3 rounded border border-border/60 bg-background/30 px-3 py-1.5"
                data-testid={`activity-row-${e.id}`}
              >
                <Activity size={11} className="mt-1 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`uppercase tracking-widest ${
                        colorByType[e.type] || "text-foreground"
                      }`}
                    >
                      {e.type.replace(/_/g, " ")}
                    </span>
                    {e.trigger_key && (
                      <Badge variant="outline">{e.trigger_key}</Badge>
                    )}
                    {Boolean(e.meta?.policy) && (
                      <Badge variant="outline">
                        policy: {String(e.meta.policy)}
                      </Badge>
                    )}
                    {e.queue_item_id && (
                      <span className="text-muted-foreground truncate text-[10px]">
                        item: {e.queue_item_id.slice(0, 8)}…
                      </span>
                    )}
                  </div>
                  {e.meta && Object.keys(e.meta).length > 0 && (
                    <div className="text-muted-foreground text-[10px] mt-0.5 truncate">
                      {Object.entries(e.meta)
                        .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
                        .join(" · ")}
                    </div>
                  )}
                </div>
                <span className="text-muted-foreground text-[10px] shrink-0">
                  {new Date(e.at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </ScrollArea>
      )}

      {!loading && items.length > 0 && (
        <div className="mt-3 flex items-center gap-2 text-[10px] text-muted-foreground font-mono">
          <AlertTriangle size={11} />
          Audit feed never persists secret values — only trigger keys, item ids and metadata.
        </div>
      )}
    </div>
  );
}
