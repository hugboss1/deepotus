import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Lock,
  Unlock,
  RefreshCcw,
  Zap,
  Settings,
  AlertTriangle,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;
const TOKEN_KEY = "deepotus_admin_token";

export default function AdminVault() {
  const navigate = useNavigate();
  const [token] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [crackTokens, setCrackTokens] = useState("1000");
  const [tokensPerDigit, setTokensPerDigit] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!token) {
      navigate("/admin");
      return;
    }
    load();
    const id = setInterval(load, 8000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function load() {
    try {
      const { data } = await axios.get(`${API}/api/admin/vault/state`, { headers });
      setState(data);
      if (tokensPerDigit === "") setTokensPerDigit(String(data.tokens_per_digit));
    } catch (e) {
      if (e?.response?.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        navigate("/admin");
        return;
      }
      toast.error("Failed to load vault state");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function doCrack() {
    const tokens = parseInt(crackTokens, 10);
    if (!Number.isFinite(tokens) || tokens <= 0) {
      toast.error("Provide a positive integer");
      return;
    }
    try {
      const { data } = await axios.post(
        `${API}/api/admin/vault/crack`,
        { tokens, agent_code: "ADMIN-CONSOLE", note: "manual crack from admin UI" },
        { headers }
      );
      setState(data);
      toast.success(`+${tokens} · digits_locked=${data.digits_locked}/${data.num_digits}`);
    } catch (e) {
      toast.error("Crack failed");
      console.error(e);
    }
  }

  async function toggleHourly(next) {
    try {
      const { data } = await axios.post(
        `${API}/api/admin/vault/config`,
        { hourly_tick_enabled: next },
        { headers }
      );
      setState(data);
      toast.success(`Hourly auto-tick ${next ? "enabled" : "disabled"}`);
    } catch (e) {
      toast.error("Config update failed");
    }
  }

  async function updateTokensPerDigit() {
    const n = parseInt(tokensPerDigit, 10);
    if (!Number.isFinite(n) || n <= 0) {
      toast.error("Invalid number");
      return;
    }
    try {
      const { data } = await axios.post(
        `${API}/api/admin/vault/config`,
        { tokens_per_digit: n },
        { headers }
      );
      setState(data);
      toast.success(`tokens_per_digit = ${n}`);
    } catch (e) {
      toast.error("Update failed");
    }
  }

  async function doReset() {
    if (!window.confirm("Reset vault? A NEW random target combination will be generated and progress wiped.")) return;
    try {
      const { data } = await axios.post(
        `${API}/api/admin/vault/config`,
        { reset: true },
        { headers }
      );
      setState(data);
      toast.success("Vault reset. New classified combination generated.");
    } catch (e) {
      toast.error("Reset failed");
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center font-mono text-sm text-muted-foreground">
        Loading vault…
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="admin-vault-page">
      <header className="border-b border-border sticky top-0 z-20 bg-background/80 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/admin")}
            className="rounded-[var(--btn-radius)]"
            data-testid="admin-vault-back"
          >
            <ArrowLeft size={16} className="mr-1" /> Admin
          </Button>
          <div className="font-display font-semibold tracking-tight">
            PROTOCOL ΔΣ · Vault Control
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-wider">
              {state?.stage}
            </Badge>
            <Button variant="outline" size="sm" onClick={load} className="rounded-[var(--btn-radius)]" data-testid="admin-vault-refresh">
              <RefreshCcw size={14} />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Classified combination */}
        <section className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-[#F59E0B] font-mono text-xs uppercase tracking-wider">
            <AlertTriangle size={14} /> CLASSIFIED · admin eyes only
          </div>
          <div className="mt-3 grid grid-cols-2 md:grid-cols-6 gap-3">
            {(state?.target_combination || []).map((d, i) => {
              const isLocked = i < (state?.digits_locked ?? 0);
              return (
                <div
                  key={i}
                  className={`rounded-lg border p-3 text-center ${isLocked ? "border-[#18C964]/50 bg-[#18C964]/10" : "border-border bg-background"}`}
                  data-testid={`admin-vault-target-${i}`}
                >
                  <div className="font-mono text-xs text-muted-foreground">Δ{i + 1}</div>
                  <div className={`font-mono text-3xl font-bold ${isLocked ? "text-[#18C964]" : "text-foreground"}`}>
                    {d}
                  </div>
                  <div className="font-mono text-[9px] uppercase tracking-widest mt-1">
                    {isLocked ? (
                      <span className="text-[#18C964] inline-flex items-center gap-1"><Lock size={10} /> locked</span>
                    ) : (
                      <span className="text-muted-foreground">pending</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
            <div>
              <div className="text-muted-foreground">digits_locked</div>
              <div className="text-foreground text-lg">{state?.digits_locked}/{state?.num_digits}</div>
            </div>
            <div>
              <div className="text-muted-foreground">tokens_sold</div>
              <div className="text-foreground text-lg">{state?.tokens_sold?.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">progress</div>
              <div className="text-foreground text-lg">{state?.progress_pct}%</div>
            </div>
            <div>
              <div className="text-muted-foreground">last_hourly_tick</div>
              <div className="text-foreground text-xs">{state?.last_hourly_tick_at || "—"}</div>
            </div>
          </div>
        </section>

        {/* Controls */}
        <section className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center gap-2 font-display font-semibold mb-3">
              <Zap size={16} /> Manual crack
            </div>
            <Label className="text-xs">Tokens to add</Label>
            <div className="flex gap-2 mt-1">
              <Input
                value={crackTokens}
                onChange={(e) => setCrackTokens(e.target.value.replace(/[^0-9]/g, ""))}
                placeholder="1000"
                className="font-mono"
                data-testid="admin-vault-crack-input"
              />
              <Button onClick={doCrack} className="rounded-[var(--btn-radius)]" data-testid="admin-vault-crack-btn">
                Crack
              </Button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Advances dials. 1 dial is locked every <strong>{state?.tokens_per_digit?.toLocaleString()}</strong> tokens.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center gap-2 font-display font-semibold mb-3">
              <Settings size={16} /> Config
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <div className="text-sm font-medium">Hourly auto-tick</div>
                <div className="text-xs text-muted-foreground">Keeps the vault alive between purchases.</div>
              </div>
              <Switch
                checked={!!state?.hourly_tick_enabled}
                onCheckedChange={toggleHourly}
                data-testid="admin-vault-hourly-toggle"
              />
            </div>
            <div className="mt-3">
              <Label className="text-xs">Tokens per digit</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  value={tokensPerDigit}
                  onChange={(e) => setTokensPerDigit(e.target.value.replace(/[^0-9]/g, ""))}
                  className="font-mono"
                  data-testid="admin-vault-tpd-input"
                />
                <Button variant="outline" onClick={updateTokensPerDigit} className="rounded-[var(--btn-radius)]" data-testid="admin-vault-tpd-save">
                  Save
                </Button>
              </div>
            </div>
            <div className="mt-5 pt-4 border-t border-border flex items-center justify-between">
              <div className="text-xs text-muted-foreground">
                Reset wipes progress and <strong>re-rolls</strong> the target.
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={doReset}
                className="rounded-[var(--btn-radius)]"
                data-testid="admin-vault-reset"
              >
                Reset
              </Button>
            </div>
          </div>
        </section>

        {/* Recent events */}
        <section className="mt-8 rounded-xl border border-border bg-card p-5">
          <div className="font-display font-semibold mb-3">Recent events</div>
          <div className="divide-y divide-border">
            {(state?.recent_events || []).map((ev) => (
              <div key={ev.id} className="flex items-center justify-between py-2 font-mono text-xs" data-testid={`admin-vault-ev-${ev.id}`}>
                <div className="flex items-center gap-3 min-w-0">
                  <Badge variant="outline" className="font-mono text-[10px] uppercase">{ev.kind}</Badge>
                  <span className="text-muted-foreground truncate">{ev.agent_code}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-foreground">+{ev.tokens_added.toLocaleString()}</span>
                  <span className="text-muted-foreground">{ev.digits_locked_before} → {ev.digits_locked_after}</span>
                  <span className="text-muted-foreground">{new Date(ev.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
            {(!state?.recent_events || state.recent_events.length === 0) && (
              <div className="text-sm text-muted-foreground py-2">No events yet.</div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
