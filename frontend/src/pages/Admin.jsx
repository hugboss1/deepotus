import React, { useEffect, useMemo, useState, useRef } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  LogOut,
  Download,
  ShieldAlert,
  RefreshCcw,
  Trash2,
  Ban,
  Plus,
  Undo2,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  UploadCloud,
  KeyRound,
  MonitorSmartphone,
  RotateCw,
  Mail,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RTooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { toast } from "sonner";
import ThemeToggle from "@/components/landing/ThemeToggle";
import ConfirmDialog from "@/components/landing/ConfirmDialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const TOKEN_KEY = "deepotus_admin_token";
const PAGE_SIZE = 25;

function formatDateShort(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-[var(--shadow-elev-1)] font-mono text-xs">
      <div className="text-foreground font-semibold">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tabular text-foreground/80">
          <span
            className="inline-block w-2 h-2 rounded-full mr-2 align-middle"
            style={{ background: p.color }}
          />
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

function StatCard({ label, value, testid }) {
  return (
    <div data-testid={testid} className="rounded-xl border border-border bg-card p-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
        {label}
      </div>
      <div className="tabular font-display font-semibold text-2xl md:text-3xl mt-1">
        {value}
      </div>
    </div>
  );
}

function Paginator({ skip, limit, total, onChange, testid }) {
  const page = Math.floor(skip / limit) + 1;
  const totalPages = Math.max(1, Math.ceil((total || 0) / limit));
  const prev = () => onChange(Math.max(0, skip - limit));
  const next = () =>
    onChange(Math.min((totalPages - 1) * limit, skip + limit));
  return (
    <div
      className="flex items-center justify-between gap-3 mt-3 font-mono text-xs"
      data-testid={testid}
    >
      <div className="text-muted-foreground">
        {total > 0
          ? `Rows ${skip + 1}–${Math.min(total, skip + limit)} / ${total}`
          : "No rows"}
      </div>
      <div className="inline-flex items-center gap-1">
        <Button
          size="sm"
          variant="outline"
          disabled={skip <= 0}
          onClick={prev}
          className="h-8 rounded-md"
          data-testid={`${testid}-prev`}
        >
          <ChevronLeft size={14} />
          Prev
        </Button>
        <span className="px-3 tabular text-foreground/80">
          {page} / {totalPages}
        </span>
        <Button
          size="sm"
          variant="outline"
          disabled={skip + limit >= total}
          onClick={next}
          className="h-8 rounded-md"
          data-testid={`${testid}-next`}
        >
          Next
          <ChevronRight size={14} />
        </Button>
      </div>
    </div>
  );
}

function EmailStatusBadge({ sent, status }) {
  if (status === "bounced" || status === "complained") {
    return (
      <span className="inline-flex items-center gap-1 text-[--campaign-red] font-mono text-xs">
        <AlertCircle size={12} /> {status}
      </span>
    );
  }
  if (status === "delivered" || status === "opened" || status === "clicked") {
    return (
      <span className="inline-flex items-center gap-1 text-[--terminal-green-dim] font-mono text-xs">
        <CheckCircle2 size={12} /> {status}
      </span>
    );
  }
  if (sent || status === "sent") {
    return (
      <span className="inline-flex items-center gap-1 text-[--amber] font-mono text-xs">
        <Mail size={12} /> sent
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-muted-foreground font-mono text-xs">
      <AlertCircle size={12} /> pending
    </span>
  );
}

export default function Admin() {
  const [token, setToken] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) || "" : "",
  );
  const [pwd, setPwd] = useState("");
  const [loading, setLoading] = useState(false);
  const [rateLimitError, setRateLimitError] = useState(null);

  const [whitelist, setWhitelist] = useState({ items: [], total: 0, skip: 0 });
  const [chatLogs, setChatLogs] = useState({ items: [], total: 0, skip: 0 });
  const [blacklist, setBlacklist] = useState({ items: [], total: 0 });
  const [sessions, setSessions] = useState({ items: [], total: 0 });
  const [stats, setStats] = useState(null);
  const [evolution, setEvolution] = useState([]);
  const [days, setDays] = useState(30);

  const [blEmail, setBlEmail] = useState("");
  const [blReason, setBlReason] = useState("");
  const [csvText, setCsvText] = useState("");
  const [importResult, setImportResult] = useState(null);
  const fileInputRef = useRef(null);

  const [confirmState, setConfirmState] = useState({
    open: false,
    mode: "delete",
    entry: null,
  });

  const navigate = useNavigate();

  useEffect(() => {
    document.title = "DEEPOTUS · Cabinet Admin";
  }, []);

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const login = async (e) => {
    e.preventDefault();
    if (!pwd.trim()) return;
    setLoading(true);
    setRateLimitError(null);
    try {
      const res = await axios.post(`${API}/admin/login`, {
        password: pwd.trim(),
      });
      localStorage.setItem(TOKEN_KEY, res.data.token);
      setToken(res.data.token);
      setPwd("");
      toast.success("Access granted. Welcome to the cabinet.");
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail || "Access denied.";
      if (status === 429) setRateLimitError(detail);
      toast.error(detail);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setWhitelist({ items: [], total: 0, skip: 0 });
    setChatLogs({ items: [], total: 0, skip: 0 });
    setBlacklist({ items: [], total: 0 });
    setSessions({ items: [], total: 0 });
    setStats(null);
    setEvolution([]);
  };

  const handleAuthError = (err) => {
    if (err?.response?.status === 401) {
      logout();
      toast.error("Session expired or revoked. Re-enter password.");
    } else {
      toast.error(err?.response?.data?.detail || "Request failed.");
    }
  };

  const loadWhitelist = async (skip = 0) => {
    try {
      const r = await axios.get(
        `${API}/admin/whitelist?limit=${PAGE_SIZE}&skip=${skip}`,
        { headers: authHeaders },
      );
      setWhitelist({ items: r.data.items || [], total: r.data.total || 0, skip });
    } catch (err) {
      handleAuthError(err);
    }
  };
  const loadChatLogs = async (skip = 0) => {
    try {
      const r = await axios.get(
        `${API}/admin/chat-logs?limit=${PAGE_SIZE}&skip=${skip}`,
        { headers: authHeaders },
      );
      setChatLogs({ items: r.data.items || [], total: r.data.total || 0, skip });
    } catch (err) {
      handleAuthError(err);
    }
  };
  const loadBlacklist = async () => {
    try {
      const r = await axios.get(`${API}/admin/blacklist?limit=500`, {
        headers: authHeaders,
      });
      setBlacklist({ items: r.data.items || [], total: r.data.total || 0 });
    } catch (err) {
      handleAuthError(err);
    }
  };
  const loadSessions = async () => {
    try {
      const r = await axios.get(`${API}/admin/sessions?limit=200`, {
        headers: authHeaders,
      });
      setSessions({ items: r.data.items || [], total: r.data.total || 0 });
    } catch (err) {
      handleAuthError(err);
    }
  };

  const loadAll = async (nextDays = days) => {
    if (!token) return;
    setLoading(true);
    try {
      const [st, ev] = await Promise.all([
        axios.get(`${API}/stats`),
        axios.get(`${API}/admin/evolution?days=${nextDays}`, { headers: authHeaders }),
      ]);
      setStats(st.data);
      setEvolution(ev.data.series || []);
      await Promise.all([loadWhitelist(0), loadChatLogs(0), loadBlacklist(), loadSessions()]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadAll(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const changeDays = async (d) => {
    setDays(d);
    try {
      const r = await axios.get(`${API}/admin/evolution?days=${d}`, {
        headers: authHeaders,
      });
      setEvolution(r.data.series || []);
    } catch (err) {
      handleAuthError(err);
    }
  };

  const exportCsv = (rows, filename) => {
    if (!rows?.length) return;
    const headers = Object.keys(rows[0]);
    const esc = (v) => {
      if (v == null) return "";
      const s = String(v).replace(/"/g, '""');
      return /[",\n]/.test(s) ? `"${s}"` : s;
    };
    const csv = [headers.join(","), ...rows.map((r) => headers.map((h) => esc(r[h])).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const askDelete = (entry) => setConfirmState({ open: true, mode: "delete", entry });
  const askBlacklist = (entry) => setConfirmState({ open: true, mode: "blacklist", entry });
  const askUnblock = (entry) => setConfirmState({ open: true, mode: "unblock", entry });
  const askRevokeSession = (entry) => setConfirmState({ open: true, mode: "revokeSession", entry });
  const askRevokeOthers = () => setConfirmState({ open: true, mode: "revokeOthers", entry: { label: "others" } });
  const askRotateSecret = () => setConfirmState({ open: true, mode: "rotateSecret", entry: { label: "secret" } });

  const doConfirmed = async () => {
    const { mode, entry } = confirmState;
    try {
      if (mode === "delete" && entry) {
        await axios.delete(`${API}/admin/whitelist/${entry.id}`, { headers: authHeaders });
        toast.success(`Deleted ${entry.email}.`);
        await loadWhitelist(whitelist.skip);
      } else if (mode === "blacklist" && entry) {
        await axios.post(`${API}/admin/whitelist/${entry.id}/blacklist`, {}, { headers: authHeaders });
        toast.success(`Blacklisted ${entry.email}.`);
        await Promise.all([loadWhitelist(whitelist.skip), loadBlacklist()]);
      } else if (mode === "unblock" && entry) {
        await axios.delete(`${API}/admin/blacklist/${entry.id}`, { headers: authHeaders });
        toast.success(`Unblocked ${entry.email}.`);
        await loadBlacklist();
      } else if (mode === "revokeSession" && entry) {
        await axios.delete(`${API}/admin/sessions/${entry.jti}`, { headers: authHeaders });
        toast.success("Session revoked.");
        if (entry.is_current) {
          logout();
        } else {
          await loadSessions();
        }
      } else if (mode === "revokeOthers") {
        const r = await axios.post(`${API}/admin/sessions/revoke-others`, {}, { headers: authHeaders });
        toast.success(r.data.message || "Revoked other sessions.");
        await loadSessions();
      } else if (mode === "rotateSecret") {
        const r = await axios.post(`${API}/admin/rotate-secret`, {}, { headers: authHeaders });
        toast.success(r.data.message || "Rotated. Please re-login.");
        // Current session will be revoked server-side → logout
        logout();
      }
      setConfirmState({ open: false, mode, entry: null });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Operation failed.");
    }
  };

  const addBlacklist = async (e) => {
    e.preventDefault();
    const v = blEmail.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      toast.error("Invalid email.");
      return;
    }
    try {
      await axios.post(
        `${API}/admin/blacklist`,
        { email: v, reason: blReason.trim() || null },
        { headers: authHeaders },
      );
      toast.success(`Blacklisted ${v}.`);
      setBlEmail("");
      setBlReason("");
      await Promise.all([loadBlacklist(), loadWhitelist(whitelist.skip)]);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to blacklist.");
    }
  };

  const onCsvFile = async (file) => {
    if (!file) return;
    try {
      const text = await file.text();
      setCsvText(text);
      toast.success(`Loaded ${file.name}. Press Import to proceed.`);
    } catch {
      toast.error("Could not read file.");
    }
  };

  const submitImport = async () => {
    if (!csvText.trim()) {
      toast.error("Paste CSV or pick a file first.");
      return;
    }
    try {
      setLoading(true);
      const res = await axios.post(
        `${API}/admin/blacklist/import`,
        { csv_text: csvText, reason: "bulk import" },
        { headers: authHeaders },
      );
      setImportResult(res.data);
      toast.success(
        `Imported ${res.data.imported}/${res.data.total_rows}. Skipped invalid: ${res.data.skipped_invalid}. Existing: ${res.data.skipped_existing}.`,
      );
      setCsvText("");
      await loadBlacklist();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Import failed.");
    } finally {
      setLoading(false);
    }
  };

  const chartData = useMemo(
    () =>
      evolution.map((p) => ({
        date: formatDateShort(p.date),
        rawDate: p.date,
        whitelist: p.whitelist,
        chat: p.chat,
      })),
    [evolution],
  );

  // ===== Login screen =====
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground p-6">
        <form
          onSubmit={login}
          className="w-full max-w-md bg-card border border-border rounded-xl p-6 md:p-8 shadow-[var(--shadow-elev-2)]"
        >
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert size={18} className="text-[--campaign-red]" />
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              — Cabinet Securé
            </div>
          </div>
          <h1 className="mt-2 font-display text-2xl md:text-3xl font-semibold">DEEPOTUS Admin Access</h1>
          <p className="mt-2 text-sm text-foreground/70">
            Entrez le mot de passe du cabinet pour consulter la whitelist et les logs de transmission.
          </p>
          <div className="mt-5">
            <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Password
            </label>
            <Input
              data-testid="admin-password-input"
              type="password"
              value={pwd}
              onChange={(e) => setPwd(e.target.value)}
              placeholder="••••••••"
              className="mt-1 font-mono"
              autoFocus
            />
          </div>
          {rateLimitError && (
            <div
              data-testid="admin-rate-limit-message"
              className="mt-3 rounded-md border border-[--campaign-red] bg-[--campaign-red]/10 px-3 py-2 font-mono text-xs text-[--campaign-red]"
            >
              {rateLimitError}
            </div>
          )}
          <Button
            type="submit"
            disabled={loading || !pwd.trim()}
            className="mt-5 w-full rounded-[var(--btn-radius)] btn-press"
            data-testid="admin-login-button"
          >
            {loading ? "…" : "Enter the Cabinet"}
          </Button>
          <div className="mt-5 flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={() => navigate("/")}
              className="text-xs font-mono text-muted-foreground hover:text-foreground transition-colors"
              data-testid="admin-back-to-site"
            >
              ← back to site
            </button>
            <ThemeToggle />
          </div>
        </form>
      </div>
    );
  }

  // ===== Dashboard =====
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <a
              href="/"
              className="font-display font-semibold tracking-tight text-base md:text-lg"
              data-testid="admin-logo"
            >
              $DEEPOTUS
            </a>
            <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              / cabinet
            </span>
            <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-widest">
              admin
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadAll(days)}
              disabled={loading}
              className="rounded-[var(--btn-radius)]"
              data-testid="admin-refresh-button"
            >
              <RefreshCcw size={14} className={`mr-1 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <ThemeToggle />
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="rounded-[var(--btn-radius)]"
              data-testid="admin-logout-button"
            >
              <LogOut size={14} className="mr-1" /> Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stat bento */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard label="Whitelist" value={stats?.whitelist_count ?? whitelist.total} testid="admin-stat-whitelist" />
          <StatCard label="Chat messages" value={stats?.chat_messages ?? chatLogs.total} testid="admin-stat-chat" />
          <StatCard label="Prophecies" value={stats?.prophecies_served ?? 0} testid="admin-stat-prophecies" />
          <StatCard label="Blacklist" value={blacklist.total} testid="admin-stat-blacklist" />
          <StatCard label="Sessions" value={sessions.total} testid="admin-stat-sessions" />
        </div>

        {/* Evolution */}
        <div className="mt-8 rounded-xl border border-border bg-card p-4 md:p-5" data-testid="admin-evolution">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">Evolution</div>
              <div className="font-display font-semibold">Whitelist & Transmissions · cumulative</div>
            </div>
            <div className="inline-flex items-center gap-1 rounded-[var(--btn-radius)] border border-border bg-background p-0.5">
              {[7, 30, 90].map((d) => {
                const active = d === days;
                return (
                  <button
                    key={d}
                    type="button"
                    onClick={() => changeDays(d)}
                    className={`px-3 py-1 rounded-[8px] font-mono text-[11px] uppercase tracking-widest transition-colors ${
                      active ? "bg-foreground text-background" : "text-foreground/70 hover:text-foreground"
                    }`}
                    data-testid={`admin-evolution-range-${d}`}
                  >
                    {d}d
                  </button>
                );
              })}
            </div>
          </div>
          <div className="h-[260px] w-full" data-testid="admin-chart-whitelist">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
                <defs>
                  <linearGradient id="gW" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2DD4BF" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#2DD4BF" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="gC" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.55} />
                    <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" tick={{ fontFamily: "IBM Plex Mono", fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={{ stroke: "hsl(var(--border))" }} />
                <YAxis tick={{ fontFamily: "IBM Plex Mono", fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={{ stroke: "hsl(var(--border))" }} allowDecimals={false} />
                <RTooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="whitelist" name="Whitelist" stroke="#2DD4BF" strokeWidth={2} fill="url(#gW)" />
                <Area type="monotone" dataKey="chat" name="Chat messages" stroke="#F59E0B" strokeWidth={2} fill="url(#gC)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <Tabs defaultValue="whitelist" className="mt-8">
          <TabsList className="flex flex-wrap gap-1 h-auto">
            <TabsTrigger value="whitelist" data-testid="admin-tab-whitelist">Whitelist ({whitelist.total})</TabsTrigger>
            <TabsTrigger value="chat" data-testid="admin-tab-chat">Chat ({chatLogs.total})</TabsTrigger>
            <TabsTrigger value="blacklist" data-testid="admin-tab-blacklist">Blacklist ({blacklist.total})</TabsTrigger>
            <TabsTrigger value="sessions" data-testid="admin-tab-sessions">Sessions ({sessions.total})</TabsTrigger>
          </TabsList>

          {/* Whitelist */}
          <TabsContent value="whitelist" className="mt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="font-display font-semibold">
                Cabinet roster · <span className="tabular font-mono text-foreground/70">{whitelist.total}</span>
              </div>
              <Button variant="outline" size="sm" disabled={!whitelist.items.length} onClick={() => exportCsv(whitelist.items, "deepotus_whitelist_page.csv")} className="rounded-[var(--btn-radius)]" data-testid="admin-export-whitelist">
                <Download size={14} className="mr-1" /> Export page CSV
              </Button>
            </div>
            <div className="rounded-xl border border-border overflow-hidden bg-card">
              <Table data-testid="admin-whitelist-table">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[70px]">#</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead className="w-[70px]">Lang</TableHead>
                    <TableHead className="w-[120px]">Email</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="w-[210px] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {whitelist.items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground py-8 font-mono text-xs">No transmissions yet.</TableCell>
                    </TableRow>
                  )}
                  {whitelist.items.map((r) => (
                    <TableRow key={r.id} data-testid={`admin-whitelist-row-${r.id}`}>
                      <TableCell className="tabular font-mono">{r.position}</TableCell>
                      <TableCell className="font-mono text-sm break-all">{r.email}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-[10px] uppercase">{r.lang}</Badge>
                      </TableCell>
                      <TableCell>
                        <EmailStatusBadge sent={r.email_sent} status={r.email_status} />
                      </TableCell>
                      <TableCell className="tabular font-mono text-xs text-foreground/70">{new Date(r.created_at).toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        <div className="inline-flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => askDelete(r)} className="h-8 rounded-md font-mono text-xs" data-testid={`admin-delete-${r.id}`}>
                            <Trash2 size={14} className="mr-1" /> Delete
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => askBlacklist(r)} className="h-8 rounded-md font-mono text-xs text-[--campaign-red] border-[--campaign-red] hover:bg-[--campaign-red] hover:text-white" data-testid={`admin-blacklist-${r.id}`}>
                            <Ban size={14} className="mr-1" /> Blacklist
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <Paginator skip={whitelist.skip} limit={PAGE_SIZE} total={whitelist.total} onChange={(s) => loadWhitelist(s)} testid="admin-whitelist-paginator" />
          </TabsContent>

          {/* Chat */}
          <TabsContent value="chat" className="mt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="font-display font-semibold">Transmissions log · <span className="tabular font-mono text-foreground/70">{chatLogs.total}</span></div>
              <Button variant="outline" size="sm" disabled={!chatLogs.items.length} onClick={() => exportCsv(chatLogs.items, "deepotus_chat_logs_page.csv")} className="rounded-[var(--btn-radius)]" data-testid="admin-export-chat">
                <Download size={14} className="mr-1" /> Export page CSV
              </Button>
            </div>
            <div className="rounded-xl border border-border bg-card divide-y divide-border" data-testid="admin-chat-list">
              {chatLogs.items.length === 0 && (
                <div className="p-8 text-center text-muted-foreground font-mono text-xs">No transmissions yet.</div>
              )}
              {chatLogs.items.map((m) => (
                <div key={m.id || m._id} className="p-4">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="font-mono text-[10px] uppercase">{m.lang}</Badge>
                      <span className="font-mono text-xs text-foreground/70 break-all">session: {m.session_id}</span>
                    </div>
                    <span className="tabular font-mono text-[10px] text-muted-foreground">{new Date(m.created_at).toLocaleString()}</span>
                  </div>
                  <div className="font-mono text-sm break-words">
                    <span className="text-[--amber]">user :~$</span>{" "}
                    <span className="text-foreground">{m.user_message}</span>
                  </div>
                  <div className="font-mono text-sm mt-1 break-words">
                    <span className="text-[--terminal-green-dim]">DEEPOTUS:~&gt;</span>{" "}
                    <span className="text-foreground/90">{m.reply}</span>
                  </div>
                </div>
              ))}
            </div>
            <Paginator skip={chatLogs.skip} limit={PAGE_SIZE} total={chatLogs.total} onChange={(s) => loadChatLogs(s)} testid="admin-chat-paginator" />
          </TabsContent>

          {/* Blacklist */}
          <TabsContent value="blacklist" className="mt-4">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-5">
                <form onSubmit={addBlacklist} className="rounded-xl border border-border bg-card p-5" data-testid="admin-blacklist-add-form">
                  <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground mb-1">Add to blacklist</div>
                  <div className="font-display font-semibold">Manual addition</div>
                  <div className="mt-3">
                    <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Email</label>
                    <Input type="email" required value={blEmail} onChange={(e) => setBlEmail(e.target.value)} placeholder="spam@example.com" className="mt-1 font-mono" data-testid="admin-blacklist-add-email" />
                  </div>
                  <div className="mt-3">
                    <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Reason (optional)</label>
                    <Input type="text" value={blReason} onChange={(e) => setBlReason(e.target.value)} placeholder="bot, abuse, DoS…" className="mt-1 font-mono" data-testid="admin-blacklist-add-reason" />
                  </div>
                  <Button type="submit" className="mt-4 w-full rounded-[var(--btn-radius)]" data-testid="admin-blacklist-add-submit">
                    <Plus size={14} className="mr-1" /> Blacklist this email
                  </Button>
                </form>

                {/* CSV import */}
                <div className="mt-4 rounded-xl border border-border bg-card p-5" data-testid="admin-blacklist-import">
                  <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground mb-1">Bulk import</div>
                  <div className="font-display font-semibold">CSV upload</div>
                  <p className="mt-2 text-xs text-foreground/70">
                    One email per line. Optional second column = reason. Max 5000 rows per import. Header row detected.
                  </p>
                  <div className="mt-3 flex items-center gap-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv,.txt,text/csv,text/plain"
                      className="hidden"
                      onChange={(e) => onCsvFile(e.target.files?.[0])}
                      data-testid="admin-blacklist-csv-file"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                      className="rounded-[var(--btn-radius)]"
                      data-testid="admin-blacklist-csv-pick"
                    >
                      <UploadCloud size={14} className="mr-1" /> Pick CSV
                    </Button>
                    <span className="font-mono text-xs text-muted-foreground">or paste below</span>
                  </div>
                  <Textarea
                    value={csvText}
                    onChange={(e) => setCsvText(e.target.value)}
                    placeholder={"email,reason\nbot1@spam.io,bot\nbot2@spam.io,abuse"}
                    className="mt-2 font-mono text-xs min-h-[120px]"
                    data-testid="admin-blacklist-csv-text"
                  />
                  <Button
                    type="button"
                    onClick={submitImport}
                    disabled={!csvText.trim() || loading}
                    className="mt-3 w-full rounded-[var(--btn-radius)]"
                    data-testid="admin-blacklist-csv-submit"
                  >
                    {loading ? "…" : "Import"}
                  </Button>
                  {importResult && (
                    <div
                      className="mt-3 rounded-md border border-border bg-background p-3 font-mono text-xs"
                      data-testid="admin-blacklist-import-result"
                    >
                      <div className="text-foreground/80">Imported: <span className="tabular text-[--terminal-green-dim]">{importResult.imported}</span></div>
                      <div className="text-foreground/80">Skipped invalid: <span className="tabular text-[--campaign-red]">{importResult.skipped_invalid}</span></div>
                      <div className="text-foreground/80">Already existed: <span className="tabular text-muted-foreground">{importResult.skipped_existing}</span></div>
                      <div className="text-foreground/80">Total rows: <span className="tabular">{importResult.total_rows}</span></div>
                    </div>
                  )}
                </div>
              </div>

              <div className="lg:col-span-7">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-display font-semibold">Blacklist roster · <span className="tabular font-mono text-foreground/70">{blacklist.total}</span></div>
                  <Button variant="outline" size="sm" disabled={!blacklist.items.length} onClick={() => exportCsv(blacklist.items, "deepotus_blacklist.csv")} className="rounded-[var(--btn-radius)]" data-testid="admin-export-blacklist">
                    <Download size={14} className="mr-1" /> Export CSV
                  </Button>
                </div>
                <div className="rounded-xl border border-border overflow-hidden bg-card">
                  <Table data-testid="admin-blacklist-table">
                    <TableHeader>
                      <TableRow>
                        <TableHead>Email</TableHead>
                        <TableHead>Reason</TableHead>
                        <TableHead>Blacklisted at</TableHead>
                        <TableHead className="w-[130px] text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {blacklist.items.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center text-muted-foreground py-8 font-mono text-xs">No blacklisted emails.</TableCell>
                        </TableRow>
                      )}
                      {blacklist.items.map((r) => (
                        <TableRow key={r.id} data-testid={`admin-blacklist-row-${r.id}`}>
                          <TableCell className="font-mono text-sm break-all">{r.email}</TableCell>
                          <TableCell className="font-mono text-xs text-foreground/70">{r.reason || "—"}</TableCell>
                          <TableCell className="tabular font-mono text-xs text-foreground/70">{r.blacklisted_at ? new Date(r.blacklisted_at).toLocaleString() : "—"}</TableCell>
                          <TableCell className="text-right">
                            <Button size="sm" variant="outline" onClick={() => askUnblock(r)} className="h-8 rounded-md font-mono text-xs" data-testid={`admin-unblock-${r.id}`}>
                              <Undo2 size={14} className="mr-1" /> Unblock
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Sessions */}
          <TabsContent value="sessions" className="mt-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
              <div className="font-display font-semibold flex items-center gap-2">
                <KeyRound size={16} /> Active admin sessions · <span className="tabular font-mono text-foreground/70">{sessions.total}</span>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={askRevokeOthers}
                  className="rounded-[var(--btn-radius)]"
                  data-testid="admin-sessions-revoke-others"
                >
                  <MonitorSmartphone size={14} className="mr-1" /> Revoke others
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={askRotateSecret}
                  className="rounded-[var(--btn-radius)] text-[--campaign-red] border-[--campaign-red] hover:bg-[--campaign-red] hover:text-white"
                  data-testid="admin-sessions-rotate-secret"
                >
                  <RotateCw size={14} className="mr-1" /> Rotate JWT secret
                </Button>
              </div>
            </div>
            <div className="rounded-xl border border-border overflow-hidden bg-card">
              <Table data-testid="admin-sessions-table">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[160px]">JTI</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Last seen</TableHead>
                    <TableHead>IP</TableHead>
                    <TableHead className="w-[150px]">Status</TableHead>
                    <TableHead className="w-[140px] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions.items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground py-8 font-mono text-xs">No active sessions.</TableCell>
                    </TableRow>
                  )}
                  {sessions.items.map((s) => (
                    <TableRow key={s.jti} data-testid={`admin-session-row-${s.jti}`}>
                      <TableCell className="font-mono text-xs break-all">{s.jti}</TableCell>
                      <TableCell className="tabular font-mono text-xs text-foreground/70">{new Date(s.created_at).toLocaleString()}</TableCell>
                      <TableCell className="tabular font-mono text-xs text-foreground/70">{s.last_seen_at ? new Date(s.last_seen_at).toLocaleString() : "—"}</TableCell>
                      <TableCell className="font-mono text-xs">{s.ip || "—"}</TableCell>
                      <TableCell>
                        {s.revoked ? (
                          <Badge variant="outline" className="font-mono text-[10px] uppercase text-[--campaign-red] border-[--campaign-red]">revoked</Badge>
                        ) : s.is_current ? (
                          <Badge className="font-mono text-[10px] uppercase bg-[--terminal-green-dim] hover:bg-[--terminal-green-dim]">current</Badge>
                        ) : (
                          <Badge variant="outline" className="font-mono text-[10px] uppercase">active</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {!s.revoked && (
                          <Button size="sm" variant="outline" onClick={() => askRevokeSession(s)} className="h-8 rounded-md font-mono text-xs" data-testid={`admin-session-revoke-${s.jti}`}>
                            <Ban size={14} className="mr-1" /> Revoke
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-3 rounded-md border border-border bg-background/60 p-3 font-mono text-[11px] text-foreground/70">
              <strong className="text-foreground">Rotate JWT secret</strong> invalidates <em>all</em> sessions immediately, including the current one. Use after any suspected compromise.
            </div>
          </TabsContent>
        </Tabs>
      </main>

      <ConfirmDialog
        open={confirmState.open}
        onOpenChange={(v) => !v && setConfirmState({ ...confirmState, open: false })}
        title={
          confirmState.mode === "blacklist"
            ? "Blacklist this email?"
            : confirmState.mode === "unblock"
            ? "Unblock this email?"
            : confirmState.mode === "revokeSession"
            ? "Revoke this session?"
            : confirmState.mode === "revokeOthers"
            ? "Revoke all other sessions?"
            : confirmState.mode === "rotateSecret"
            ? "Rotate JWT secret?"
            : "Delete this entry?"
        }
        description={
          confirmState.mode === "blacklist"
            ? `${confirmState.entry?.email || ""} will be removed from the whitelist and added to the blacklist.`
            : confirmState.mode === "unblock"
            ? `${confirmState.entry?.email || ""} will be removed from the blacklist and can register again.`
            : confirmState.mode === "revokeSession"
            ? `Session ${confirmState.entry?.jti || ""} will be revoked immediately.${confirmState.entry?.is_current ? " This is YOUR current session — you will be logged out." : ""}`
            : confirmState.mode === "revokeOthers"
            ? "All other admin sessions (except this one) will be revoked immediately."
            : confirmState.mode === "rotateSecret"
            ? "The JWT signing secret will be rotated. ALL active sessions, including yours, will be revoked. You will be logged out and must re-enter the password."
            : `${confirmState.entry?.email || ""} will be removed from the whitelist. It can still re-register later.`
        }
        confirmLabel={
          confirmState.mode === "blacklist"
            ? "Blacklist"
            : confirmState.mode === "unblock"
            ? "Unblock"
            : confirmState.mode === "revokeSession"
            ? "Revoke"
            : confirmState.mode === "revokeOthers"
            ? "Revoke others"
            : confirmState.mode === "rotateSecret"
            ? "Rotate secret"
            : "Delete"
        }
        cancelLabel="Cancel"
        destructive={confirmState.mode !== "unblock"}
        onConfirm={doConfirmed}
        testIdPrefix="admin-confirm"
      />
    </div>
  );
}
