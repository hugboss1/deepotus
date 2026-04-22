import React, { useEffect, useState } from "react";
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
import { LogOut, Download, ShieldAlert, RefreshCcw } from "lucide-react";
import { toast } from "sonner";
import ThemeToggle from "@/components/landing/ThemeToggle";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const TOKEN_KEY = "deepotus_admin_token";

export default function Admin() {
  const [token, setToken] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) || "" : "",
  );
  const [pwd, setPwd] = useState("");
  const [loading, setLoading] = useState(false);
  const [whitelist, setWhitelist] = useState([]);
  const [chatLogs, setChatLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "DEEPOTUS · Cabinet Admin";
  }, []);

  const login = async (e) => {
    e.preventDefault();
    if (!pwd.trim()) return;
    setLoading(true);
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
      toast.error("Access denied.");
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
  };

  const authHeaders = token ? { "X-Admin-Token": token } : {};

  const loadAll = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [wl, cl, st] = await Promise.all([
        axios.get(`${API}/admin/whitelist`, { headers: authHeaders }),
        axios.get(`${API}/admin/chat-logs`, { headers: authHeaders }),
        axios.get(`${API}/stats`),
      ]);
      setWhitelist(wl.data.items || []);
      setChatLogs(cl.data.items || []);
      setStats(st.data);
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
    if (token) loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

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
      {/* Top bar */}
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
              onClick={loadAll}
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
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {whitelist.length === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={4}
                        className="text-center text-muted-foreground py-8 font-mono text-xs"
                      >
                        No transmissions yet.
                      </TableCell>
                    </TableRow>
                  )}
                  {whitelist.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="tabular font-mono">
                        {r.position}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {r.email}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-[10px] uppercase">
                          {r.lang}
                        </Badge>
                      </TableCell>
                      <TableCell className="tabular font-mono text-xs text-foreground/70">
                        {new Date(r.created_at).toLocaleString()}
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
                      <span className="font-mono text-xs text-foreground/70">
                        session: {m.session_id}
                      </span>
                    </div>
                    <span className="tabular font-mono text-[10px] text-muted-foreground">
                      {new Date(m.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="font-mono text-sm">
                    <span className="text-[--amber]">user :~$</span>{" "}
                    <span className="text-foreground">{m.user_message}</span>
                  </div>
                  <div className="font-mono text-sm mt-1">
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
