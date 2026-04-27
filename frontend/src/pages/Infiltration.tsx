/**
 * PROTOCOL ΔΣ — Pre-Launch Infiltration Brain admin panel (Sprint 14.1).
 *
 * Surface tabs:
 *   • Riddles       — CRUD the 5 Proof-of-Intelligence enigmas
 *   • Clearance     — ledger of agents + their level 0..3
 *   • Sleeper Cell  — pre-launch kill-switch for market triggers + buy links
 *   • Attempts      — audit tail of recent riddle submissions
 *
 * Admin JWT carried via ``getAdminToken()``; 2FA enforced server-side for
 * every mutation so the UI just surfaces the 403 with a toast.
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  Activity,
  ArrowLeft,
  Binary,
  BookLock,
  CheckCircle2,
  Download,
  Eye,
  EyeOff,
  Loader2,
  MoonStar,
  Pencil,
  Plus,
  ShieldCheck,
  ShieldOff,
  Trash2,
  Users,
  Wallet,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

import { getAdminToken } from "@/lib/adminAuth";
import { logger } from "@/lib/logger";

const API: string = process.env.REACT_APP_BACKEND_URL || "";

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------
interface Riddle {
  id: string;
  slug: string;
  order: number;
  title: string;
  question_fr: string;
  question_en: string;
  accepted_keywords: string[];
  hint: string | null;
  enabled: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

interface ClearanceRow {
  id: string;
  email: string;
  wallet_address: string | null;
  level: number;
  riddles_solved: string[];
  level_1_achieved_at: string | null;
  level_2_achieved_at: string | null;
  level_3_achieved_at: string | null;
  wallet_linked_at: string | null;
  created_at: string;
  updated_at: string;
  notes: string | null;
  source: string | null;
}

interface ClearanceStats {
  total: number;
  level_1: number;
  level_2: number;
  level_3: number;
  with_wallet: number;
  airdrop_eligible: number;
}

interface SleeperState {
  active: boolean;
  message_fr: string;
  message_en: string;
  blocked_triggers: string[];
  activated_at: string | null;
  deactivated_at: string | null;
  version: number;
}

interface Attempt {
  id: string;
  slug: string;
  email: string | null;
  correct: boolean;
  matched_keyword: string | null;
  at: string;
  answer_excerpt: string;
}

// ---------------------------------------------------------------------
// Helpers
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
    toast.error("2FA required", {
      description: "Enable 2FA from Admin → Security first.",
    });
    return;
  }
  toast.error(typeof detail === "string" ? detail : fallback);
  logger.error(err);
}

// ---------------------------------------------------------------------
// Root page
// ---------------------------------------------------------------------
export default function Infiltration() {
  const navigate = useNavigate();
  const token = getAdminToken();
  const [tab, setTab] = useState<string>("riddles");

  useEffect(() => {
    if (!token) navigate("/admin");
  }, [token, navigate]);

  return (
    <div
      className="min-h-screen bg-background text-foreground p-6 md:p-10"
      data-testid="infiltration-page"
    >
      <header className="max-w-6xl mx-auto mb-8">
        <button
          type="button"
          onClick={() => navigate("/admin")}
          className="text-xs uppercase tracking-[0.3em] text-muted-foreground hover:text-foreground inline-flex items-center gap-2 mb-4"
          data-testid="infiltration-back"
        >
          <ArrowLeft size={14} /> Back to dashboard
        </button>
        <div className="text-[10px] tracking-[0.4em] text-muted-foreground uppercase">
          $DEEPOTUS / PROTOCOL ΔΣ
        </div>
        <h1 className="text-2xl md:text-3xl font-medium mt-1">
          Infiltration Brain
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
          Riddles of the Terminal, Clearance ledger, Sleeper Cell kill-switch.
          Every mutation below is 2FA-gated — if you land on a 403, re-enable
          2FA from the Security tab.
        </p>
      </header>

      <main className="max-w-6xl mx-auto">
        <Tabs value={tab} onValueChange={setTab} className="w-full">
          <TabsList className="grid grid-cols-4 w-full md:w-auto">
            <TabsTrigger value="riddles" data-testid="infiltration-tab-riddles">
              <BookLock size={14} className="mr-2" /> Riddles
            </TabsTrigger>
            <TabsTrigger value="clearance" data-testid="infiltration-tab-clearance">
              <Users size={14} className="mr-2" /> Clearance
            </TabsTrigger>
            <TabsTrigger value="sleeper" data-testid="infiltration-tab-sleeper">
              <MoonStar size={14} className="mr-2" /> Sleeper Cell
            </TabsTrigger>
            <TabsTrigger value="attempts" data-testid="infiltration-tab-attempts">
              <Activity size={14} className="mr-2" /> Attempts
            </TabsTrigger>
          </TabsList>

          <TabsContent value="riddles" className="mt-6">
            <RiddlesTab />
          </TabsContent>
          <TabsContent value="clearance" className="mt-6">
            <ClearanceTab />
          </TabsContent>
          <TabsContent value="sleeper" className="mt-6">
            <SleeperTab />
          </TabsContent>
          <TabsContent value="attempts" className="mt-6">
            <AttemptsTab />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------
// Riddles tab
// ---------------------------------------------------------------------
function RiddlesTab() {
  const [items, setItems] = useState<Riddle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [editing, setEditing] = useState<Riddle | "new" | null>(null);
  const [revealedId, setRevealedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<{ items: Riddle[] }>(
        `${API}/api/admin/infiltration/riddles`,
        { headers: authHeaders() },
      );
      setItems(data.items);
    } catch (err) {
      handleError(err, "Failed to load riddles");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const remove = async (id: string) => {
    if (!window.confirm("Delete this riddle?")) return;
    try {
      await axios.delete(`${API}/api/admin/infiltration/riddles/${id}`, {
        headers: authHeaders(),
      });
      toast.success("Riddle deleted");
      await load();
    } catch (err) {
      handleError(err, "Failed to delete");
    }
  };

  const toggle = async (r: Riddle) => {
    try {
      await axios.patch(
        `${API}/api/admin/infiltration/riddles/${r.id}`,
        { enabled: !r.enabled },
        { headers: authHeaders() },
      );
      await load();
    } catch (err) {
      handleError(err, "Failed to toggle");
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
      <div className="flex justify-between items-center">
        <p className="text-[11px] text-muted-foreground">
          {items.length} riddles seeded. Keywords are matched case-insensitively
          after accent normalisation.
        </p>
        <Button
          onClick={() => setEditing("new")}
          className="rounded-[var(--btn-radius)]"
          data-testid="riddle-new"
        >
          <Plus size={14} className="mr-1" /> New riddle
        </Button>
      </div>

      {items.map((r) => (
        <div
          key={r.id}
          className="rounded-md border border-border bg-background/40 p-4"
          data-testid={`riddle-row-${r.slug}`}
        >
          <div className="flex items-start gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <Badge variant="outline" className="font-mono">
                  #{r.order}
                </Badge>
                <span className="text-sm font-medium">{r.title}</span>
                <Badge variant="outline" className="font-mono text-[10px]">
                  {r.slug}
                </Badge>
                {!r.enabled && <Badge variant="secondary">disabled</Badge>}
              </div>
              <p className="text-[12px] text-foreground/80 mt-1">
                {r.question_fr}
              </p>
              <div className="mt-2 flex items-center gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={() =>
                    setRevealedId(revealedId === r.id ? null : r.id)
                  }
                  className="text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
                  data-testid={`riddle-reveal-keywords-${r.slug}`}
                >
                  {revealedId === r.id ? (
                    <>
                      <EyeOff size={11} /> Hide keywords
                    </>
                  ) : (
                    <>
                      <Eye size={11} /> Reveal {r.accepted_keywords.length} keywords
                    </>
                  )}
                </button>
                {revealedId === r.id && (
                  <div className="flex flex-wrap gap-1">
                    {r.accepted_keywords.map((kw) => (
                      <Badge
                        key={kw}
                        className="bg-[#F59E0B] text-black font-mono text-[10px]"
                      >
                        {kw}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Switch
                checked={r.enabled}
                onCheckedChange={() => toggle(r)}
                data-testid={`riddle-toggle-${r.slug}`}
              />
              <Button
                size="icon"
                variant="ghost"
                onClick={() => setEditing(r)}
                data-testid={`riddle-edit-${r.slug}`}
              >
                <Pencil size={14} />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                onClick={() => remove(r.id)}
                data-testid={`riddle-delete-${r.slug}`}
              >
                <Trash2 size={14} className="text-[#FF4D4D]" />
              </Button>
            </div>
          </div>
        </div>
      ))}

      {editing && (
        <RiddleEditor
          riddle={editing === "new" ? null : editing}
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

interface RiddleEditorProps {
  riddle: Riddle | null;
  onClose: () => void;
  onSaved: () => void;
}

function RiddleEditor({ riddle, onClose, onSaved }: RiddleEditorProps) {
  const [busy, setBusy] = useState<boolean>(false);
  const [slug, setSlug] = useState<string>(riddle?.slug || "");
  const [title, setTitle] = useState<string>(riddle?.title || "");
  const [questionFr, setQuestionFr] = useState<string>(riddle?.question_fr || "");
  const [questionEn, setQuestionEn] = useState<string>(riddle?.question_en || "");
  const [keywordsText, setKeywordsText] = useState<string>(
    (riddle?.accepted_keywords || []).join(", "),
  );
  const [hint, setHint] = useState<string>(riddle?.hint || "");
  const [order, setOrder] = useState<number>(riddle?.order || 100);
  const [enabled, setEnabled] = useState<boolean>(riddle?.enabled ?? true);

  const submit = async () => {
    const kws = keywordsText.split(",").map((k) => k.trim()).filter(Boolean);
    if (kws.length === 0) {
      toast.error("At least one keyword is required");
      return;
    }
    setBusy(true);
    try {
      if (riddle) {
        await axios.patch(
          `${API}/api/admin/infiltration/riddles/${riddle.id}`,
          {
            title,
            question_fr: questionFr,
            question_en: questionEn,
            accepted_keywords: kws,
            hint: hint || null,
            order,
            enabled,
          },
          { headers: authHeaders() },
        );
        toast.success("Riddle updated");
      } else {
        await axios.post(
          `${API}/api/admin/infiltration/riddles`,
          {
            slug,
            title,
            question_fr: questionFr,
            question_en: questionEn,
            accepted_keywords: kws,
            hint: hint || null,
            order,
            enabled,
          },
          { headers: authHeaders() },
        );
        toast.success("Riddle created");
      }
      onSaved();
    } catch (err) {
      handleError(err, "Failed to save riddle");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={(v: boolean) => !v && onClose()}>
      <DialogContent className="max-w-2xl" data-testid="riddle-editor">
        <DialogHeader>
          <DialogTitle>
            {riddle ? "Edit riddle" : "New riddle"}
          </DialogTitle>
          <DialogDescription>
            Keywords are <strong>case-insensitive + accent-insensitive</strong>{" "}
            substring matches. A single word that appears in any expected
            answer is enough.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs uppercase tracking-widest">Slug</Label>
              <Input
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="grand-architecte"
                disabled={!!riddle || busy}
                className="font-mono"
                data-testid="riddle-slug"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-widest">Order</Label>
              <Input
                type="number"
                value={order}
                onChange={(e) => setOrder(Number(e.target.value))}
                disabled={busy}
                className="font-mono"
                data-testid="riddle-order"
              />
            </div>
          </div>

          <div>
            <Label className="text-xs uppercase tracking-widest">Title</Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={busy}
              data-testid="riddle-title"
            />
          </div>

          <div>
            <Label className="text-xs uppercase tracking-widest">Question (FR)</Label>
            <Textarea
              value={questionFr}
              onChange={(e) => setQuestionFr(e.target.value)}
              rows={4}
              disabled={busy}
              className="text-sm"
              data-testid="riddle-question-fr"
            />
          </div>

          <div>
            <Label className="text-xs uppercase tracking-widest">Question (EN)</Label>
            <Textarea
              value={questionEn}
              onChange={(e) => setQuestionEn(e.target.value)}
              rows={4}
              disabled={busy}
              className="text-sm"
              data-testid="riddle-question-en"
            />
          </div>

          <div>
            <Label className="text-xs uppercase tracking-widest">
              Accepted keywords (comma separated)
            </Label>
            <Textarea
              value={keywordsText}
              onChange={(e) => setKeywordsText(e.target.value)}
              rows={2}
              disabled={busy}
              placeholder="la fed, planche a billets, inflation"
              className="font-mono text-sm"
              data-testid="riddle-keywords"
            />
          </div>

          <div>
            <Label className="text-xs uppercase tracking-widest">
              Hint (optional, shown after 3 wrong attempts)
            </Label>
            <Input
              value={hint}
              onChange={(e) => setHint(e.target.value)}
              disabled={busy}
              data-testid="riddle-hint"
            />
          </div>

          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <Switch
              checked={enabled}
              onCheckedChange={setEnabled}
              disabled={busy}
              data-testid="riddle-enabled"
            />
            <span>Enabled</span>
          </label>
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
            data-testid="riddle-save"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------
// Clearance tab
// ---------------------------------------------------------------------
function ClearanceTab() {
  const [stats, setStats] = useState<ClearanceStats | null>(null);
  const [rows, setRows] = useState<ClearanceRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [levelFilter, setLevelFilter] = useState<string>("all");
  const [editing, setEditing] = useState<ClearanceRow | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, l] = await Promise.all([
        axios.get<ClearanceStats>(
          `${API}/api/admin/infiltration/clearance/stats`,
          { headers: authHeaders() },
        ),
        axios.get<{ items: ClearanceRow[] }>(
          `${API}/api/admin/infiltration/clearance`,
          {
            headers: authHeaders(),
            params: levelFilter !== "all" ? { level: levelFilter } : {},
          },
        ),
      ]);
      setStats(s.data);
      setRows(l.data.items);
    } catch (err) {
      handleError(err, "Failed to load clearance ledger");
    } finally {
      setLoading(false);
    }
  }, [levelFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const downloadCsv = async () => {
    try {
      const { data } = await axios.get(
        `${API}/api/admin/infiltration/clearance/snapshot.csv`,
        { headers: authHeaders(), responseType: "blob" },
      );
      const url = URL.createObjectURL(
        new Blob([data], { type: "text/csv" }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = "deepotus_level3_snapshot.csv";
      a.click();
      URL.revokeObjectURL(url);
      toast.success("CSV downloaded.");
    } catch (err) {
      handleError(err, "Failed to download snapshot");
    }
  };

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="animate-spin" size={20} />
      </div>
    );
  }

  const statCards = [
    { key: "total", label: "Total agents", value: stats.total },
    { key: "level_1", label: "Level 1", value: stats.level_1 },
    { key: "level_2", label: "Level 2", value: stats.level_2 },
    { key: "level_3", label: "Level 3", value: stats.level_3 },
    { key: "with_wallet", label: "With wallet", value: stats.with_wallet },
    {
      key: "airdrop",
      label: "Airdrop eligible",
      value: stats.airdrop_eligible,
      accent: true,
    },
  ];

  return (
    <div className="space-y-4">
      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        {statCards.map((c) => (
          <div
            key={c.key}
            className={`rounded-md border ${
              c.accent
                ? "border-[#18C964]/50 bg-[#18C964]/5"
                : "border-border bg-background/40"
            } p-3`}
            data-testid={`clearance-stat-${c.key}`}
          >
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
              {c.label}
            </div>
            <div
              className={`text-2xl font-mono ${
                c.accent ? "text-[#18C964]" : "text-foreground"
              } tabular`}
            >
              {c.value}
            </div>
          </div>
        ))}
      </div>

      {/* Filters + CSV */}
      <div className="flex items-center gap-3 flex-wrap">
        <Select value={levelFilter} onValueChange={setLevelFilter}>
          <SelectTrigger className="h-9 w-[140px] text-xs" data-testid="clearance-level-filter">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All levels</SelectItem>
            <SelectItem value="0">Level 0</SelectItem>
            <SelectItem value="1">Level 1</SelectItem>
            <SelectItem value="2">Level 2</SelectItem>
            <SelectItem value="3">Level 3 (airdrop)</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          onClick={downloadCsv}
          className="rounded-[var(--btn-radius)] ml-auto"
          data-testid="clearance-csv"
        >
          <Download size={14} className="mr-1" /> Snapshot CSV
        </Button>
      </div>

      {/* Rows */}
      {rows.length === 0 ? (
        <div className="text-center text-sm text-muted-foreground py-12">
          No agents match this filter.
        </div>
      ) : (
        <div className="space-y-2">
          {rows.map((r) => (
            <div
              key={r.id}
              className="rounded-md border border-border bg-background/40 p-3"
              data-testid={`clearance-row-${r.email}`}
            >
              <div className="flex items-start gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="font-mono">
                      L{r.level}
                    </Badge>
                    <span className="text-sm font-mono truncate">{r.email}</span>
                    {r.wallet_address && (
                      <Badge className="bg-[#18C964] text-black font-mono text-[10px] flex items-center gap-1">
                        <Wallet size={10} />
                        {r.wallet_address.slice(0, 4)}…{r.wallet_address.slice(-4)}
                      </Badge>
                    )}
                    {r.level === 3 && !r.wallet_address && (
                      <Badge className="bg-[#F59E0B] text-black font-mono text-[10px]">
                        NEEDS WALLET
                      </Badge>
                    )}
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-1 font-mono">
                    {r.riddles_solved.length} riddles solved ·{" "}
                    {r.source || "—"} · updated{" "}
                    {new Date(r.updated_at).toLocaleString()}
                  </div>
                  {r.notes && (
                    <div className="text-[11px] text-[#F59E0B] mt-1 font-mono">
                      note: {r.notes}
                    </div>
                  )}
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditing(r)}
                  className="rounded-[var(--btn-radius)]"
                  data-testid={`clearance-edit-${r.email}`}
                >
                  <Pencil size={13} className="mr-1" /> Adjust
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {editing && (
        <ClearanceEditor
          row={editing}
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

interface ClearanceEditorProps {
  row: ClearanceRow;
  onClose: () => void;
  onSaved: () => void;
}

function ClearanceEditor({ row, onClose, onSaved }: ClearanceEditorProps) {
  const [busy, setBusy] = useState<boolean>(false);
  const [level, setLevel] = useState<number>(row.level);
  const [wallet, setWallet] = useState<string>(row.wallet_address || "");
  const [notes, setNotes] = useState<string>(row.notes || "");

  const submit = async () => {
    setBusy(true);
    try {
      await axios.patch(
        `${API}/api/admin/infiltration/clearance/${encodeURIComponent(row.email)}`,
        {
          level,
          wallet_address: wallet || null,
          notes: notes || null,
        },
        { headers: authHeaders() },
      );
      toast.success("Agent updated");
      onSaved();
    } catch (err) {
      handleError(err, "Failed to update agent");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={(v: boolean) => !v && onClose()}>
      <DialogContent className="max-w-md" data-testid="clearance-editor">
        <DialogHeader>
          <DialogTitle>Adjust agent — {row.email}</DialogTitle>
          <DialogDescription>
            Operator override. Used to manually promote Level 1+2 while the X /
            Telegram verifiers are waiting on Sprint 14.2.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <Label className="text-xs uppercase tracking-widest">Level</Label>
            <Select
              value={String(level)}
              onValueChange={(v: string) => setLevel(Number(v))}
            >
              <SelectTrigger className="font-mono" data-testid="clearance-editor-level">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">0 — Prospect</SelectItem>
                <SelectItem value="1">1 — Observer</SelectItem>
                <SelectItem value="2">2 — Infiltrator</SelectItem>
                <SelectItem value="3">3 — Agent (airdrop eligible)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs uppercase tracking-widest">
              Wallet (Solana, base58)
            </Label>
            <Input
              value={wallet}
              onChange={(e) => setWallet(e.target.value)}
              disabled={busy}
              className="font-mono text-xs"
              data-testid="clearance-editor-wallet"
            />
          </div>
          <div>
            <Label className="text-xs uppercase tracking-widest">Notes</Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              maxLength={500}
              disabled={busy}
              className="text-xs"
              data-testid="clearance-editor-notes"
            />
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
            data-testid="clearance-editor-save"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : "Apply"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------
// Sleeper Cell tab
// ---------------------------------------------------------------------
function SleeperTab() {
  const [state, setState] = useState<SleeperState | null>(null);
  const [busy, setBusy] = useState<boolean>(false);
  const [msgFr, setMsgFr] = useState<string>("");
  const [msgEn, setMsgEn] = useState<string>("");
  const [blocked, setBlocked] = useState<string[]>([]);

  const load = useCallback(async () => {
    try {
      const { data } = await axios.get<SleeperState>(
        `${API}/api/admin/infiltration/sleeper-cell`,
        { headers: authHeaders() },
      );
      setState(data);
      setMsgFr(data.message_fr);
      setMsgEn(data.message_en);
      setBlocked(data.blocked_triggers || []);
    } catch (err) {
      handleError(err, "Failed to load sleeper state");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async (patch: Partial<SleeperState>) => {
    setBusy(true);
    try {
      const { data } = await axios.patch<SleeperState>(
        `${API}/api/admin/infiltration/sleeper-cell`,
        patch,
        { headers: authHeaders() },
      );
      setState(data);
      let toastMsg: string;
      if (patch.active === undefined) {
        toastMsg = "Settings saved";
      } else if (patch.active) {
        toastMsg = "Sleeper cell ENGAGED";
      } else {
        toastMsg = "Sleeper cell STOOD DOWN";
      }
      toast.success(toastMsg);
    } catch (err) {
      handleError(err, "Failed to update sleeper state");
    } finally {
      setBusy(false);
    }
  };

  if (!state) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="animate-spin" size={20} />
      </div>
    );
  }

  const allTriggers = ["mint", "whale_buy", "mc_milestone", "raydium_migration", "jeet_dip"];

  return (
    <div className="space-y-6">
      {/* Toggle card */}
      <div
        className={`rounded-md border p-5 ${
          state.active
            ? "border-[#F59E0B] bg-[#F59E0B]/10"
            : "border-[#18C964]/40 bg-[#18C964]/5"
        }`}
        data-testid="sleeper-toggle-card"
      >
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-2 text-[10px] tracking-[0.3em] uppercase text-muted-foreground">
              <MoonStar size={12} /> Pre-launch kill-switch
            </div>
            <div
              className={`text-sm font-mono mt-2 ${
                state.active ? "text-[#F59E0B]" : "text-[#18C964]"
              }`}
              data-testid="sleeper-status"
            >
              {state.active ? "SLEEPER CELL ACTIVE" : "OPERATIONAL"}
            </div>
            <p className="text-[11px] text-muted-foreground mt-1 max-w-xl">
              {state.active
                ? "Market triggers are blocked and the landing page hides every buy link. Only the Proof of Intelligence terminal stays open."
                : "Full engine live. Market triggers flow to the approval queue; buy links are visible."}
            </p>
          </div>
          <Button
            variant={state.active ? "default" : "destructive"}
            onClick={() => save({ active: !state.active })}
            disabled={busy}
            className="rounded-[var(--btn-radius)] min-w-[140px]"
            data-testid="sleeper-toggle"
          >
            {(() => {
              if (busy) return <Loader2 size={14} className="animate-spin" />;
              if (state.active) {
                return (
                  <>
                    <ShieldCheck size={14} className="mr-1" /> Stand down
                  </>
                );
              }
              return (
                <>
                  <ShieldOff size={14} className="mr-1" /> Engage
                </>
              );
            })()}
          </Button>
        </div>
      </div>

      {/* Messages + blocked triggers */}
      <div className="rounded-md border border-border bg-background/40 p-5 space-y-4">
        <h3 className="text-sm font-medium flex items-center gap-2">
          <Binary size={14} /> Public messaging
        </h3>
        <div>
          <Label className="text-xs uppercase tracking-widest">Message (FR)</Label>
          <Textarea
            value={msgFr}
            onChange={(e) => setMsgFr(e.target.value)}
            rows={3}
            maxLength={500}
            className="text-sm"
            data-testid="sleeper-message-fr"
          />
        </div>
        <div>
          <Label className="text-xs uppercase tracking-widest">Message (EN)</Label>
          <Textarea
            value={msgEn}
            onChange={(e) => setMsgEn(e.target.value)}
            rows={3}
            maxLength={500}
            className="text-sm"
            data-testid="sleeper-message-en"
          />
        </div>

        <div>
          <Label className="text-xs uppercase tracking-widest mb-2 block">
            Blocked triggers (while active)
          </Label>
          <div className="flex flex-wrap gap-2">
            {allTriggers.map((t) => {
              const on = blocked.includes(t);
              return (
                <button
                  key={t}
                  type="button"
                  onClick={() =>
                    setBlocked(
                      on ? blocked.filter((x) => x !== t) : [...blocked, t],
                    )
                  }
                  className={`px-3 py-1 rounded-full text-[11px] font-mono border ${
                    on
                      ? "bg-[#F59E0B] text-black border-[#F59E0B]"
                      : "bg-background text-foreground/70 border-border hover:border-foreground/40"
                  }`}
                  data-testid={`sleeper-block-${t}`}
                >
                  {t}
                </button>
              );
            })}
          </div>
        </div>

        <Button
          onClick={() =>
            save({
              message_fr: msgFr,
              message_en: msgEn,
              blocked_triggers: blocked,
            })
          }
          disabled={busy}
          className="rounded-[var(--btn-radius)]"
          data-testid="sleeper-save"
        >
          {busy ? <Loader2 size={14} className="animate-spin" /> : "Save messaging"}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------
// Attempts audit tab
// ---------------------------------------------------------------------
function AttemptsTab() {
  const [items, setItems] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterEmail, setFilterEmail] = useState<string>("");
  const [filterSlug, setFilterSlug] = useState<string>("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<{ items: Attempt[] }>(
        `${API}/api/admin/infiltration/attempts`,
        {
          headers: authHeaders(),
          params: {
            ...(filterEmail ? { email: filterEmail } : {}),
            ...(filterSlug ? { slug: filterSlug } : {}),
            limit: 200,
          },
        },
      );
      setItems(data.items);
    } catch (err) {
      handleError(err, "Failed to load attempts");
    } finally {
      setLoading(false);
    }
  }, [filterEmail, filterSlug]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 flex-wrap">
        <Input
          placeholder="Filter by email"
          value={filterEmail}
          onChange={(e) => setFilterEmail(e.target.value)}
          className="h-9 w-[220px] text-xs"
          data-testid="attempts-filter-email"
        />
        <Input
          placeholder="Filter by riddle slug"
          value={filterSlug}
          onChange={(e) => setFilterSlug(e.target.value)}
          className="h-9 w-[220px] text-xs"
          data-testid="attempts-filter-slug"
        />
      </div>
      {(() => {
        if (loading) {
          return (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="animate-spin" size={20} />
            </div>
          );
        }
        if (items.length === 0) {
          return (
            <div className="text-center text-sm text-muted-foreground py-12">
              No attempts match.
            </div>
          );
        }
        return (
          <div className="space-y-1.5 font-mono text-[11px]">
            {items.map((a) => (
              <div
                key={a.id}
                className="flex items-center gap-3 rounded border border-border/60 bg-background/30 px-3 py-1.5"
                data-testid={`attempt-row-${a.id}`}
              >
                <span className="text-muted-foreground shrink-0">
                  {new Date(a.at).toLocaleTimeString()}
                </span>
                {a.correct ? (
                  <CheckCircle2 size={12} className="text-[#18C964] shrink-0" />
                ) : (
                  <span className="text-[#FF4D4D] shrink-0">✗</span>
                )}
                <Badge variant="outline" className="shrink-0">
                  {a.slug}
                </Badge>
                {a.email && (
                  <span className="text-foreground/80 truncate">{a.email}</span>
                )}
                <span className="text-muted-foreground truncate flex-1">
                  "{a.answer_excerpt}"
                </span>
                {a.matched_keyword && (
                  <Badge className="bg-[#18C964]/20 text-[#18C964] font-mono text-[10px] shrink-0">
                    {a.matched_keyword}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        );
      })()}
    </div>
  );
}
