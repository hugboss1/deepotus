import React, { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  getAdminToken,
  setAdminToken,
  clearAdminToken,
} from "@/lib/adminAuth";
import {
  LogOut,
  ShieldAlert,
  RefreshCcw,
  Mail,
  Bot,
} from "lucide-react";
import { toast } from "sonner";
import ThemeToggle from "@/components/landing/ThemeToggle";
import ConfirmDialog from "@/components/landing/ConfirmDialog";
import TwoFASetupDialog from "@/components/admin/TwoFASetupDialog";

import { StatCard } from "./admin/components/StatCard";
import { EvolutionChart } from "./admin/components/EvolutionChart";
import { AdminLogin } from "./admin/components/AdminLogin";
import { WhitelistTab } from "./admin/sections/WhitelistTab";
import { ChatLogsTab } from "./admin/sections/ChatLogsTab";
import { BlacklistTab } from "./admin/sections/BlacklistTab";
import { SessionsTab } from "./admin/sections/SessionsTab";

import type {
  AdminEvolutionPoint,
  AdminSession,
  AdminStatsResponse,
  BlacklistEntry,
  BlacklistImportResult,
  ChatLogEntry,
  ConfirmMode,
  ConfirmState,
  PaginatedState,
  TwoFAStatus,
  WhitelistEntry,
} from "@/types";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const PAGE_SIZE = 25;

const emptyState = <T,>(): PaginatedState<T> => ({ items: [], total: 0, skip: 0 });

export default function Admin() {
  const [token, setToken] = useState<string>(() => getAdminToken() || "");
  const [pwd, setPwd] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [rateLimitError, setRateLimitError] = useState<string | null>(null);

  const [whitelist, setWhitelist] = useState<PaginatedState<WhitelistEntry>>(emptyState<WhitelistEntry>());
  const [chatLogs, setChatLogs] = useState<PaginatedState<ChatLogEntry>>(emptyState<ChatLogEntry>());
  const [blacklist, setBlacklist] = useState<PaginatedState<BlacklistEntry>>(emptyState<BlacklistEntry>());
  const [sessions, setSessions] = useState<PaginatedState<AdminSession>>(emptyState<AdminSession>());
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [evolution, setEvolution] = useState<AdminEvolutionPoint[]>([]);
  const [days, setDays] = useState<number>(30);

  const [blEmail, setBlEmail] = useState<string>("");
  const [blReason, setBlReason] = useState<string>("");
  const [blCooldown, setBlCooldown] = useState<string>("");
  const [csvText, setCsvText] = useState<string>("");
  const [csvCooldown, setCsvCooldown] = useState<string>("");
  const [importResult, setImportResult] = useState<BlacklistImportResult | null>(null);

  const [totpCode, setTotpCode] = useState<string>("");
  const [twofaRequired, setTwofaRequired] = useState<boolean>(false);
  const [twofaStatus, setTwofaStatus] = useState<TwoFAStatus | null>(null);
  const [twofaDialogOpen, setTwofaDialogOpen] = useState<boolean>(false);

  const [confirmState, setConfirmState] = useState<ConfirmState>({
    open: false,
    mode: "delete",
    entry: null,
  });

  useEffect(() => {
    document.title = "DEEPOTUS · Cabinet Admin";
  }, []);

  const authHeaders = React.useMemo(
    () => (token ? { Authorization: `Bearer ${token}` } : {}),
    [token],
  );

  const login = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pwd.trim()) return;
    setLoading(true);
    setRateLimitError(null);
    try {
      const body: { password: string; totp_code?: string } = { password: pwd.trim() };
      if (totpCode.trim()) body.totp_code = totpCode.trim();
      const res = await axios.post(`${API}/admin/login`, body);
      setAdminToken(res.data.token);
      setToken(res.data.token);
      setPwd("");
      setTotpCode("");
      setTwofaRequired(false);
      toast.success("Access granted. Welcome to the cabinet.");
    } catch (err: unknown) {
      // eslint-disable-next-line
      const e2 = err as any;
      const status = e2?.response?.status;
      const detail = e2?.response?.data?.detail || "Access denied.";
      const twofaHeader = e2?.response?.headers?.["x-2fa-required"];
      if (status === 401 && (detail === "2FA required" || twofaHeader === "true")) {
        setTwofaRequired(true);
        toast.message("2FA required — enter your 6-digit code.");
      } else {
        if (status === 429) setRateLimitError(detail);
        if (status === 401 && detail === "Invalid 2FA code") setTwofaRequired(true);
        toast.error(detail);
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearAdminToken();
    setToken("");
    setWhitelist(emptyState<WhitelistEntry>());
    setChatLogs(emptyState<ChatLogEntry>());
    setBlacklist(emptyState<BlacklistEntry>());
    setSessions(emptyState<AdminSession>());
    setStats(null);
    setEvolution([]);
  };

  // eslint-disable-next-line
  const handleAuthError = (err: any) => {
    if (err?.response?.status === 401) {
      logout();
      toast.error("Session expired or revoked. Re-enter password.");
    } else {
      toast.error(err?.response?.data?.detail || "Request failed.");
    }
  };

  const loadWhitelist = async (skip = 0) => {
    try {
      const r = await axios.get(`${API}/admin/whitelist?limit=${PAGE_SIZE}&skip=${skip}`, { headers: authHeaders });
      setWhitelist({ items: r.data.items || [], total: r.data.total || 0, skip });
    } catch (err) {
      handleAuthError(err);
    }
  };

  const loadChatLogs = async (skip = 0) => {
    try {
      const r = await axios.get(`${API}/admin/chat-logs?limit=${PAGE_SIZE}&skip=${skip}`, { headers: authHeaders });
      setChatLogs({ items: r.data.items || [], total: r.data.total || 0, skip });
    } catch (err) {
      handleAuthError(err);
    }
  };

  const loadBlacklist = async () => {
    try {
      const r = await axios.get(`${API}/admin/blacklist?limit=500`, { headers: authHeaders });
      setBlacklist({ items: r.data.items || [], total: r.data.total || 0, skip: 0 });
    } catch (err) {
      handleAuthError(err);
    }
  };

  const loadSessions = async () => {
    try {
      const r = await axios.get(`${API}/admin/sessions?limit=200`, { headers: authHeaders });
      setSessions({ items: r.data.items || [], total: r.data.total || 0, skip: 0 });
    } catch (err) {
      handleAuthError(err);
    }
  };

  const load2FA = async () => {
    try {
      const r = await axios.get(`${API}/admin/2fa/status`, { headers: authHeaders });
      setTwofaStatus(r.data);
    } catch (err) {
      handleAuthError(err);
    }
  };

  const disable2FA = async () => {
    const code = window.prompt("Enter your current 6-digit TOTP code (or a backup code) to disable 2FA:");
    if (!code || !code.trim()) return;
    try {
      await axios.post(
        `${API}/admin/2fa/disable`,
        { password: window.prompt("Confirm password:") || "", code: code.trim() },
        { headers: authHeaders },
      );
      toast.success("2FA disabled.");
      await load2FA();
    } catch (err: unknown) {
      // eslint-disable-next-line
      toast.error((err as any)?.response?.data?.detail || "Failed to disable 2FA.");
    }
  };

  const downloadFullWhitelist = async () => {
    try {
      const res = await axios.get(`${API}/admin/whitelist/export`, { headers: authHeaders, responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "deepotus_whitelist_full.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success("Full whitelist exported.");
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
      await Promise.all([
        loadWhitelist(0),
        loadChatLogs(0),
        loadBlacklist(),
        loadSessions(),
        load2FA(),
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadAll(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const changeDays = async (d: number) => {
    setDays(d);
    try {
      const r = await axios.get(`${API}/admin/evolution?days=${d}`, { headers: authHeaders });
      setEvolution(r.data.series || []);
    } catch (err) {
      handleAuthError(err);
    }
  };

  // eslint-disable-next-line
  const exportCsv = (rows: any[], filename: string) => {
    if (!rows?.length) return;
    const headers = Object.keys(rows[0]);
    // eslint-disable-next-line
    const esc = (v: any) => {
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

  // eslint-disable-next-line
  const askConfirm = (mode: ConfirmMode, entry: any) =>
    setConfirmState({ open: true, mode, entry });

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
        logout();
      }
      setConfirmState({ open: false, mode, entry: null });
    } catch (err: unknown) {
      // eslint-disable-next-line
      toast.error((err as any)?.response?.data?.detail || "Operation failed.");
    }
  };

  const addBlacklist = async (e: React.FormEvent) => {
    e.preventDefault();
    const v = blEmail.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      toast.error("Invalid email.");
      return;
    }
    const cd = parseInt(blCooldown, 10);
    try {
      await axios.post(
        `${API}/admin/blacklist`,
        { email: v, reason: blReason.trim() || null, cooldown_days: cd > 0 ? cd : null },
        { headers: authHeaders },
      );
      toast.success(cd > 0 ? `Blacklisted ${v} for ${cd} day(s).` : `Blacklisted ${v} permanently.`);
      setBlEmail("");
      setBlReason("");
      setBlCooldown("");
      await Promise.all([loadBlacklist(), loadWhitelist(whitelist.skip)]);
    } catch (err: unknown) {
      // eslint-disable-next-line
      toast.error((err as any)?.response?.data?.detail || "Failed to blacklist.");
    }
  };

  const onCsvFile = async (file: File | undefined) => {
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
    const cd = parseInt(csvCooldown, 10);
    try {
      setLoading(true);
      const res = await axios.post(
        `${API}/admin/blacklist/import`,
        { csv_text: csvText, reason: "bulk import", cooldown_days: cd > 0 ? cd : null },
        { headers: authHeaders },
      );
      setImportResult(res.data);
      toast.success(
        `Imported ${res.data.imported}/${res.data.total_rows}. Skipped invalid: ${res.data.skipped_invalid}. Existing: ${res.data.skipped_existing}.`,
      );
      setCsvText("");
      setCsvCooldown("");
      await loadBlacklist();
    } catch (err: unknown) {
      // eslint-disable-next-line
      toast.error((err as any)?.response?.data?.detail || "Import failed.");
    } finally {
      setLoading(false);
    }
  };

  // ===== Login screen =====
  if (!token) {
    return (
      <AdminLogin
        pwd={pwd}
        setPwd={setPwd}
        totpCode={totpCode}
        setTotpCode={setTotpCode}
        twofaRequired={twofaRequired}
        rateLimitError={rateLimitError}
        loading={loading}
        onSubmit={login}
      />
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
            <Button asChild variant="outline" size="sm" className="rounded-[var(--btn-radius)]" data-testid="admin-emails-link">
              <Link to="/admin/emails">
                <Mail size={14} className="mr-1" /> Email events
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm" className="rounded-[var(--btn-radius)]" data-testid="admin-vault-link">
              <Link to="/admin/vault">
                <ShieldAlert size={14} className="mr-1" /> Vault · PROTOCOL ΔΣ
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm" className="rounded-[var(--btn-radius)]" data-testid="admin-bots-link">
              <Link to="/admin/bots">
                <Bot size={14} className="mr-1" /> Bots Fleet
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm" className="rounded-[var(--btn-radius)]" data-testid="admin-cabinet-vault-link">
              <Link to="/admin/cabinet-vault">
                <ShieldAlert size={14} className="mr-1" /> Cabinet Vault
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm" className="rounded-[var(--btn-radius)]" data-testid="admin-propaganda-link">
              <Link to="/admin/propaganda">
                <Bot size={14} className="mr-1" /> Propaganda Engine
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm" className="rounded-[var(--btn-radius)]" data-testid="admin-infiltration-link">
              <Link to="/admin/infiltration">
                <ShieldAlert size={14} className="mr-1" /> Infiltration Brain
              </Link>
            </Button>
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
            <Button variant="outline" size="sm" onClick={logout} className="rounded-[var(--btn-radius)]" data-testid="admin-logout-button">
              <LogOut size={14} className="mr-1" /> Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard label="Whitelist" value={stats?.whitelist_count ?? whitelist.total} testid="admin-stat-whitelist" />
          <StatCard label="Chat messages" value={stats?.chat_messages ?? chatLogs.total} testid="admin-stat-chat" />
          <StatCard label="Prophecies" value={stats?.prophecies_served ?? 0} testid="admin-stat-prophecies" />
          <StatCard label="Blacklist" value={blacklist.total} testid="admin-stat-blacklist" />
          <StatCard label="Sessions" value={sessions.total} testid="admin-stat-sessions" />
        </div>

        <EvolutionChart evolution={evolution} days={days} onChangeDays={changeDays} />

        <Tabs defaultValue="whitelist" className="mt-8">
          <TabsList className="flex flex-wrap gap-1 h-auto">
            <TabsTrigger value="whitelist" data-testid="admin-tab-whitelist">Whitelist ({whitelist.total})</TabsTrigger>
            <TabsTrigger value="chat" data-testid="admin-tab-chat">Chat ({chatLogs.total})</TabsTrigger>
            <TabsTrigger value="blacklist" data-testid="admin-tab-blacklist">Blacklist ({blacklist.total})</TabsTrigger>
            <TabsTrigger value="sessions" data-testid="admin-tab-sessions">Security ({sessions.total})</TabsTrigger>
          </TabsList>

          <TabsContent value="whitelist" className="mt-4">
            <WhitelistTab
              whitelist={whitelist}
              pageSize={PAGE_SIZE}
              onLoad={loadWhitelist}
              onExportPage={() => exportCsv(whitelist.items, "deepotus_whitelist_page.csv")}
              onExportFull={downloadFullWhitelist}
              onAskDelete={(entry) => askConfirm("delete", entry)}
              onAskBlacklist={(entry) => askConfirm("blacklist", entry)}
            />
          </TabsContent>

          <TabsContent value="chat" className="mt-4">
            <ChatLogsTab
              chatLogs={chatLogs}
              pageSize={PAGE_SIZE}
              onLoad={loadChatLogs}
              onExport={() => exportCsv(chatLogs.items, "deepotus_chat_logs_page.csv")}
            />
          </TabsContent>

          <TabsContent value="blacklist" className="mt-4">
            <BlacklistTab
              blacklist={blacklist}
              blEmail={blEmail}
              setBlEmail={setBlEmail}
              blReason={blReason}
              setBlReason={setBlReason}
              blCooldown={blCooldown}
              setBlCooldown={setBlCooldown}
              csvText={csvText}
              setCsvText={setCsvText}
              csvCooldown={csvCooldown}
              setCsvCooldown={setCsvCooldown}
              importResult={importResult}
              loading={loading}
              onAddBlacklist={addBlacklist}
              onCsvFile={onCsvFile}
              onSubmitImport={submitImport}
              onAskUnblock={(entry) => askConfirm("unblock", entry)}
              onExport={() => exportCsv(blacklist.items, "deepotus_blacklist.csv")}
            />
          </TabsContent>

          <TabsContent value="sessions" className="mt-4">
            <SessionsTab
              api={API}
              headers={authHeaders as { Authorization: string }}
              sessions={sessions}
              twofaStatus={twofaStatus}
              onAskRevokeSession={(entry) => askConfirm("revokeSession", entry)}
              onAskRevokeOthers={() => askConfirm("revokeOthers", { label: "others" })}
              onAskRotateSecret={() => askConfirm("rotateSecret", { label: "secret" })}
              onEnable2FA={() => setTwofaDialogOpen(true)}
              onDisable2FA={disable2FA}
            />
          </TabsContent>
        </Tabs>
      </main>

      {(() => {
        // Confirm-dialog copy lookup — replaces a 6-level nested ternary.
        // Each mode maps to {title, description, confirmLabel}. Falls back
        // to the "delete" copy when the mode is unrecognised so the UI
        // stays sensible during transitional states.
        const entry = confirmState.entry;
        const sessionDesc = `Session ${entry?.jti || ""} will be revoked immediately.${
          entry?.is_current
            ? " This is YOUR current session — you will be logged out."
            : ""
        }`;
        const dict: Record<
          ConfirmMode,
          { title: string; description: string; confirmLabel: string }
        > = {
          blacklist: {
            title: "Blacklist this email?",
            description: `${entry?.email || ""} will be removed from the whitelist and added to the blacklist.`,
            confirmLabel: "Blacklist",
          },
          unblock: {
            title: "Unblock this email?",
            description: `${entry?.email || ""} will be removed from the blacklist and can register again.`,
            confirmLabel: "Unblock",
          },
          revokeSession: {
            title: "Revoke this session?",
            description: sessionDesc,
            confirmLabel: "Revoke",
          },
          revokeOthers: {
            title: "Revoke all other sessions?",
            description: "All other admin sessions (except this one) will be revoked immediately.",
            confirmLabel: "Revoke others",
          },
          rotateSecret: {
            title: "Rotate JWT secret?",
            description:
              "The JWT signing secret will be rotated. ALL active sessions, including yours, will be revoked. You will be logged out and must re-enter the password.",
            confirmLabel: "Rotate secret",
          },
          delete: {
            title: "Delete this entry?",
            description: `${entry?.email || ""} will be removed from the whitelist. It can still re-register later.`,
            confirmLabel: "Delete",
          },
        };
        const copy = dict[confirmState.mode] ?? dict.delete;
        return (
          <ConfirmDialog
            open={confirmState.open}
            onOpenChange={(v: boolean) =>
              !v && setConfirmState({ ...confirmState, open: false })
            }
            title={copy.title}
            description={copy.description}
            confirmLabel={copy.confirmLabel}
            cancelLabel="Cancel"
            destructive={confirmState.mode !== "unblock"}
            onConfirm={doConfirmed}
            testIdPrefix="admin-confirm"
          />
        );
      })()}
      <TwoFASetupDialog
        open={twofaDialogOpen}
        onOpenChange={setTwofaDialogOpen}
        token={token}
        onCompleted={() => {
          load2FA();
        }}
      />
    </div>
  );
}
