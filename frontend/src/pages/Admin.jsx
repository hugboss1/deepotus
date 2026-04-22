import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
          <span className="inline-block w-2 h-2 rounded-full mr-2 align-middle" style={{ background: p.color }} />
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

export default function Admin() {
  const [token, setToken] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) || "" : "",
  );
  const [pwd, setPwd] = useState("");
  const [loading, setLoading] = useState(false);
  const [whitelist, setWhitelist] = useState([]);
  const [chatLogs, setChatLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [evolution, setEvolution] = useState([]);
  const [days, setDays] = useState(30);
  const [rateLimitError, setRateLimitError] = useState(null);
  const [confirmState, setConfirmState] = useState({
    open: false,
    mode: "delete",
    entry: null,
  });
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "DEEPOTUS · Cabinet Admin";
  }, []);

  const login = async (e) => {
    e.preventDefault();
    if (!pwd.trim()) return;
    setLoading(true);
    setRateLimitError(null);
    try {
      const res = await axios.post(`${API}/admin/login`, {
        password: pwd.trim(),
      });
      const tkn = res.data.token;
      localStorage.setItem(TOKEN_KEY, tkn);
      setToken(tkn);
      setPwd("");
      toast.success("Access granted. Welcome to the cabinet.");
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail || "Access denied.";
      if (status === 429) {
        setRateLimitError(detail);
        toast.error(detail);
      } else {
        toast.error(detail);
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setWhitelist([]);
    setChatLogs([]);
    setStats(null);
    setEvolution([]);
  };

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const loadAll = async (nextDays = days) => {
    if (!token) return;
    setLoading(true);
    try {
      const [wl, cl, st, ev] = await Promise.all([
        axios.get(`${API}/admin/whitelist`, { headers: authHeaders }),
        axios.get(`${API}/admin/chat-logs`, { headers: authHeaders }),
        axios.get(`${API}/stats`),
        axios.get(`${API}/admin/evolution?days=${nextDays}`, {
          headers: authHeaders,
        }),
      ]);
      setWhitelist(wl.data.items || []);
      setChatLogs(cl.data.items || []);
      setStats(st.data);
      setEvolution(ev.data.series || []);
    } catch (err) {
      if (err?.response?.status === 401) {
        logout();
        toast.error("Session expired. Re-enter password.");
      } else {
        toast.error("Failed to fetch data.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadAll(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const changeDays = (d) => {
    setDays(d);
    loadAll(d);
  };

  const exportCsv = (rows, filename) => {
    if (!rows?.length) return;
    const headers = Object.keys(rows[0]);
    const esc = (v) => {
      if (v == null) return "";
      const s = String(v).replace(/"/g, '""');
      return /[",\n]/.test(s) ? `"${s}"` : s;
    };
    const csv = [
      headers.join(","),
      ...rows.map((r) => headers.map((h) => esc(r[h])).join(",")),
    ].join("\n");
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

  const askDelete = (entry) =>
    setConfirmState({ open: true, mode: "delete", entry });
  const askBlacklist = (entry) =>
    setConfirmState({ open: true, mode: "blacklist", entry });

  const doConfirmed = async () => {
    const { mode, entry } = confirmState;
    if (!entry) return;
    try {
      if (mode === "delete") {
        await axios.delete(`${API}/admin/whitelist/${entry.id}`, {
          headers: authHeaders,
        });
        toast.success(`Deleted ${entry.email}.`);
      } else if (mode === "blacklist") {
        await axios.post(
          `${API}/admin/whitelist/${entry.id}/blacklist`,
          {},
          { headers: authHeaders },
        );
        toast.success(`Blacklisted ${entry.email}.`);
      }
      setConfirmState({ open: false, mode, entry: null });
      await loadAll(days);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Operation failed.");
    }
  };

  const chartData = useMemo(
    () =>
      evolution.map((p) => ({
        date: formatDateShort(p.date),
        rawDate: p.date,
        whitelist: p.whitelist,
        chat: p.chat,
        whitelist_daily: p.whitelist_daily,
        chat_daily: p.chat_daily,
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
          <h1 className="mt-2 font-display text-2xl md:text-3xl font-semibold">
            DEEPOTUS Admin Access
          </h1>
          <p className="mt-2 text-sm text-foreground/70">
            Entrez le mot de passe du cabinet pour consulter la whitelist et les
            logs de transmission.
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
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-widest"
            >
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
              <RefreshCcw
                size={14}
                className={`mr-1 ${loading ? "animate-spin" : ""}`}
              />
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
        {/* Stats bento */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Whitelist"
            value={stats?.whitelist_count ?? whitelist.length}
            testid="admin-stat-whitelist"
          />
          <StatCard
            label="Chat messages"
            value={stats?.chat_messages ?? chatLogs.length}
            testid="admin-stat-chat"
          />
          <StatCard
            label="Prophecies served"
            value={stats?.prophecies_served ?? 0}
            testid="admin-stat-prophecies"
          />
          <StatCard
            label="Launch"
            value={
              stats?.launch_timestamp
                ? new Date(stats.launch_timestamp).toLocaleDateString()
                : "—"
            }
            testid="admin-stat-launch"
          />
        </div>

        {/* Evolution charts */}
        <div className="mt-8 rounded-xl border border-border bg-card p-4 md:p-5" data-testid="admin-evolution">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                Evolution
              </div>
              <div className="font-display font-semibold">
                Whitelist & Transmissions · cumulative
              </div>
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
                      active
                        ? "bg-foreground text-background"
                        : "text-foreground/70 hover:text-foreground"
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
              <AreaChart
                data={chartData}
                margin={{ top: 8, right: 12, left: -18, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="gWhitelist" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2DD4BF" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#2DD4BF" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="gChat" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.55} />
                    <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="date"
                  tick={{
                    fontFamily: "IBM Plex Mono",
                    fontSize: 11,
                    fill: "hsl(var(--muted-foreground))",
                  }}
                  tickLine={false}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                />
                <YAxis
                  tick={{
                    fontFamily: "IBM Plex Mono",
                    fontSize: 11,
                    fill: "hsl(var(--muted-foreground))",
                  }}
                  tickLine={false}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  allowDecimals={false}
                />
                <RTooltip content={<ChartTooltip />} />
                <Area
                  type="monotone"
                  dataKey="whitelist"
                  name="Whitelist"
                  stroke="#2DD4BF"
                  strokeWidth={2}
                  fill="url(#gWhitelist)"
                />
                <Area
                  type="monotone"
                  dataKey="chat"
                  name="Chat messages"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  fill="url(#gChat)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#2DD4BF]" />
              Whitelist (cumulative)
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
              Chat transmissions (cumulative)
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="whitelist" className="mt-8">
          <TabsList>
            <TabsTrigger value="whitelist" data-testid="admin-tab-whitelist">
              Whitelist ({whitelist.length})
            </TabsTrigger>
            <TabsTrigger value="chat" data-testid="admin-tab-chat">
              Chat Logs ({chatLogs.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="whitelist" className="mt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="font-display font-semibold">
                Cabinet roster ·{" "}
                <span className="tabular font-mono text-foreground/70">
                  {whitelist.length}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                disabled={!whitelist.length}
                onClick={() => exportCsv(whitelist, "deepotus_whitelist.csv")}
                className="rounded-[var(--btn-radius)]"
                data-testid="admin-export-whitelist"
              >
                <Download size={14} className="mr-1" /> Export CSV
              </Button>
            </div>
            <div className="rounded-xl border border-border overflow-hidden bg-card">
              <Table data-testid="admin-whitelist-table">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[70px]">#</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead className="w-[80px]">Lang</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="w-[180px] text-right">
                      Actions
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {whitelist.length === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        className="text-center text-muted-foreground py-8 font-mono text-xs"
                      >
                        No transmissions yet.
                      </TableCell>
                    </TableRow>
                  )}
                  {whitelist.map((r) => (
                    <TableRow key={r.id} data-testid={`admin-whitelist-row-${r.id}`}>
                      <TableCell className="tabular font-mono">
                        {r.position}
                      </TableCell>
                      <TableCell className="font-mono text-sm break-all">
                        {r.email}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className="font-mono text-[10px] uppercase"
                        >
                          {r.lang}
                        </Badge>
                      </TableCell>
                      <TableCell className="tabular font-mono text-xs text-foreground/70">
                        {new Date(r.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="inline-flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => askDelete(r)}
                            className="h-8 rounded-md font-mono text-xs"
                            data-testid={`admin-delete-${r.id}`}
                            title="Delete"
                          >
                            <Trash2 size={14} className="mr-1" />
                            Delete
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => askBlacklist(r)}
                            className="h-8 rounded-md font-mono text-xs text-[--campaign-red] border-[--campaign-red] hover:bg-[--campaign-red] hover:text-white"
                            data-testid={`admin-blacklist-${r.id}`}
                            title="Blacklist"
                          >
                            <Ban size={14} className="mr-1" />
                            Blacklist
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value="chat" className="mt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="font-display font-semibold">
                Transmissions log ·{" "}
                <span className="tabular font-mono text-foreground/70">
                  {chatLogs.length}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                disabled={!chatLogs.length}
                onClick={() => exportCsv(chatLogs, "deepotus_chat_logs.csv")}
                className="rounded-[var(--btn-radius)]"
                data-testid="admin-export-chat"
              >
                <Download size={14} className="mr-1" /> Export CSV
              </Button>
            </div>
            <div
              className="rounded-xl border border-border bg-card divide-y divide-border"
              data-testid="admin-chat-list"
            >
              {chatLogs.length === 0 && (
                <div className="p-8 text-center text-muted-foreground font-mono text-xs">
                  No transmissions yet.
                </div>
              )}
              {chatLogs.map((m) => (
                <div key={m.id || m._id} className="p-4">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className="font-mono text-[10px] uppercase"
                      >
                        {m.lang}
                      </Badge>
                      <span className="font-mono text-xs text-foreground/70 break-all">
                        session: {m.session_id}
                      </span>
                    </div>
                    <span className="tabular font-mono text-[10px] text-muted-foreground">
                      {new Date(m.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="font-mono text-sm break-words">
                    <span className="text-[--amber]">user :~$</span>{" "}
                    <span className="text-foreground">{m.user_message}</span>
                  </div>
                  <div className="font-mono text-sm mt-1 break-words">
                    <span className="text-[--terminal-green-dim]">
                      DEEPOTUS:~&gt;
                    </span>{" "}
                    <span className="text-foreground/90">{m.reply}</span>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </main>

      <ConfirmDialog
        open={confirmState.open}
        onOpenChange={(v) =>
          !v && setConfirmState({ ...confirmState, open: false })
        }
        title={
          confirmState.mode === "blacklist"
            ? "Blacklist this email?"
            : "Delete this entry?"
        }
        description={
          confirmState.mode === "blacklist"
            ? `The email ${confirmState.entry?.email || ""} will be removed from the whitelist and added to the blacklist. It cannot register again until you remove it from the blacklist manually.`
            : `The entry ${confirmState.entry?.email || ""} will be removed from the whitelist. It can still re-register later.`
        }
        confirmLabel={
          confirmState.mode === "blacklist" ? "Blacklist" : "Delete"
        }
        cancelLabel="Cancel"
        destructive
        onConfirm={doConfirmed}
        testIdPrefix="admin-confirm"
      />
    </div>
  );
}

function StatCard({ label, value, testid }) {
  return (
    <div
      data-testid={testid}
      className="rounded-xl border border-border bg-card p-4"
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
        {label}
      </div>
      <div className="tabular font-display font-semibold text-2xl md:text-3xl mt-1">
        {value}
      </div>
    </div>
  );
}
