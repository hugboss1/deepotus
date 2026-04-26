import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { getAdminToken, setAdminToken, clearAdminToken } from "@/lib/adminAuth";
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
  Radio,
  Play,
  ExternalLink,
} from "lucide-react";
import { logger } from "@/lib/logger";
import HeliusSection from "@/pages/admin/sections/HeliusSection";
import SealStatusSection from "@/pages/admin/sections/SealStatusSection";

const API = process.env.REACT_APP_BACKEND_URL;

export default function AdminVault() {
  const navigate = useNavigate();
  const [token] = useState(() => getAdminToken());
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [crackTokens, setCrackTokens] = useState("1000");
  const [tokensPerDigit, setTokensPerDigit] = useState("");
  const [tokensPerMicro, setTokensPerMicro] = useState("");
  const [treasuryGoal, setTreasuryGoal] = useState("");
  const [eurUsdRate, setEurUsdRate] = useState("");
  const [dexCustomAddr, setDexCustomAddr] = useState("");
  const [dexPollBusy, setDexPollBusy] = useState(false);
  const [dexLastPoll, setDexLastPoll] = useState(null);

  // Helius state has moved to <HeliusSection /> (Sprint 6 split).

  // Memoize headers so child sections don't re-fire effects every render
  // when their parent re-renders (token rarely changes, headers stay stable).
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}` }),
    [token],
  );

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
      if (tokensPerMicro === "") setTokensPerMicro(String(data.tokens_per_micro ?? 100000));
      if (treasuryGoal === "") setTreasuryGoal(String(data.treasury_goal_eur ?? 300000));
      if (eurUsdRate === "") setEurUsdRate(String(data.eur_usd_rate ?? 1.08));
      if (dexCustomAddr === "" && data.dex_token_address) setDexCustomAddr(data.dex_token_address);
    } catch (e) {
      if (e?.response?.status === 401) {
        clearAdminToken();
        navigate("/admin");
        return;
      }
      toast.error("Failed to load vault state");
      logger.error(e);
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
      logger.error(e);
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
      toast.success(`tokens_per_digit = ${n.toLocaleString()}`);
    } catch (e) {
      toast.error("Update failed");
    }
  }

  async function updateTokensPerMicro() {
    const n = parseInt(tokensPerMicro, 10);
    if (!Number.isFinite(n) || n <= 0) {
      toast.error("Invalid number");
      return;
    }
    try {
      const { data } = await axios.post(
        `${API}/api/admin/vault/config`,
        { tokens_per_micro: n },
        { headers }
      );
      setState(data);
      toast.success(`tokens_per_micro = ${n.toLocaleString()}`);
    } catch (e) {
      toast.error("Update failed");
    }
  }

  async function updateTreasuryCfg() {
    const g = parseFloat(treasuryGoal);
    const r = parseFloat(eurUsdRate);
    if (!Number.isFinite(g) || g <= 0 || !Number.isFinite(r) || r <= 0) {
      toast.error("Invalid values");
      return;
    }
    try {
      const { data } = await axios.post(
        `${API}/api/admin/vault/config`,
        { treasury_goal_eur: g, eur_usd_rate: r },
        { headers }
      );
      setState(data);
      toast.success(`Treasury goal=€${g} · rate=${r}`);
    } catch (e) {
      toast.error("Update failed");
    }
  }

  async function applyPreset(preset) {
    try {
      const { data } = await axios.post(
        `${API}/api/admin/vault/config`,
        { preset },
        { headers }
      );
      setState(data);
      setTokensPerDigit(String(data.tokens_per_digit));
      setTokensPerMicro(String(data.tokens_per_micro));
      setTreasuryGoal(String(data.treasury_goal_eur));
      setEurUsdRate(String(data.eur_usd_rate));
      toast.success(`Preset applied: ${preset.toUpperCase()}`);
    } catch (e) {
      toast.error("Preset failed");
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

  async function setDexMode(mode) {
    try {
      const payload = { mode };
      if (mode === "custom") payload.token_address = dexCustomAddr.trim();
      const { data } = await axios.post(
        `${API}/api/admin/vault/dex-config`,
        payload,
        { headers }
      );
      setState(data);
      toast.success(`DEX mode → ${mode}`);
    } catch (e) {
      toast.error("DEX config failed");
      logger.error(e);
    }
  }

  async function forcePoll() {
    setDexPollBusy(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/vault/dex-poll`,
        {},
        { headers }
      );
      setDexLastPoll(data);
      if (data.skipped) {
        toast.info(`Skipped: ${data.error || "no changes"}`);
      } else {
        toast.success(
          `Polled ${data.pair} · +${data.delta_buys || 0} buys · ${data.ticks_applied} tick(s)`
        );
      }
      await load();
    } catch (e) {
      toast.error("Poll failed");
      logger.error(e);
    } finally {
      setDexPollBusy(false);
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
                  key={`admin-vault-target-dial-${i}`}
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

            {/* PRESET BUTTONS */}
            <div className="mb-4 p-3 rounded-md border border-[#F59E0B]/30 bg-[#F59E0B]/5">
              <div className="text-xs font-medium text-foreground mb-2">Quick presets</div>
              <div className="flex gap-2 flex-wrap">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => applyPreset("production")}
                  className="rounded-[var(--btn-radius)] border-[#18C964]/40"
                  data-testid="admin-vault-preset-production"
                >
                  Production (100M / 10K)
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => applyPreset("demo")}
                  className="rounded-[var(--btn-radius)] border-[#F59E0B]/40"
                  data-testid="admin-vault-preset-demo"
                >
                  Demo (1K / 100)
                </Button>
              </div>
              <p className="mt-2 text-[11px] text-muted-foreground">
                Production: 600M tokens to fully crack (300K€ at €0.0005) · Demo: fast crack for testing
              </p>
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
              <Label className="text-xs">Tokens per digit (1 dial lock)</Label>
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

            <div className="mt-3">
              <Label className="text-xs">Tokens per micro-rotation</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  value={tokensPerMicro}
                  onChange={(e) => setTokensPerMicro(e.target.value.replace(/[^0-9]/g, ""))}
                  className="font-mono"
                  data-testid="admin-vault-tpm-input"
                />
                <Button variant="outline" onClick={updateTokensPerMicro} className="rounded-[var(--btn-radius)]" data-testid="admin-vault-tpm-save">
                  Save
                </Button>
              </div>
              <p className="mt-1 text-[11px] text-muted-foreground">
                Every N tokens bought = 1 dial spin animation (no lock)
              </p>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-2">
              <div>
                <Label className="text-xs">Treasury goal (€)</Label>
                <Input
                  value={treasuryGoal}
                  onChange={(e) => setTreasuryGoal(e.target.value.replace(/[^0-9.]/g, ""))}
                  className="font-mono mt-1"
                  data-testid="admin-vault-goal-input"
                />
              </div>
              <div>
                <Label className="text-xs">EUR/USD rate</Label>
                <Input
                  value={eurUsdRate}
                  onChange={(e) => setEurUsdRate(e.target.value.replace(/[^0-9.]/g, ""))}
                  className="font-mono mt-1"
                  data-testid="admin-vault-rate-input"
                />
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={updateTreasuryCfg}
              className="mt-2 rounded-[var(--btn-radius)]"
              data-testid="admin-vault-treasury-save"
            >
              Save treasury config
            </Button>
            <p className="mt-1 text-[11px] text-muted-foreground">
              If treasury EUR value ≥ goal (custom mode only) → force DECLASSIFIED.
            </p>

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

        {/* DEX Integration (DexScreener) */}
        <section className="mt-8 rounded-xl border border-border bg-card p-5" data-testid="admin-vault-dex-section">
          <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
            <div className="flex items-center gap-2 font-display font-semibold">
              <Radio size={16} className={state?.dex_mode !== "off" ? "text-[#2DD4BF] animate-pulse" : "text-muted-foreground"} />
              DEX Live Feed · DexScreener
            </div>
            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className={`font-mono text-[10px] uppercase ${state?.dex_mode === "off" ? "" : "border-[#2DD4BF]/50 text-[#2DD4BF]"}`}
                data-testid="admin-dex-mode-badge"
              >
                {state?.dex_mode || "off"}
              </Badge>
              {state?.dex_label && (
                <Badge variant="outline" className="font-mono text-[10px]">
                  {state.dex_label}
                </Badge>
              )}
            </div>
          </div>

          <p className="text-xs text-muted-foreground mb-4">
            Polls DexScreener every 30s to detect real buy activity on Solana. Custom mode: 1 tick per{" "}
            <strong>{state?.tokens_per_digit?.toLocaleString()}</strong> tokens bought. Demo mode uses BONK with symbolic ticks.
          </p>

          {/* Mode selector */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            {["off", "demo", "custom"].map((m) => (
              <Button
                key={m}
                variant={state?.dex_mode === m ? "default" : "outline"}
                size="sm"
                onClick={() => setDexMode(m)}
                disabled={m === "custom" && !dexCustomAddr.trim()}
                className="rounded-[var(--btn-radius)]"
                data-testid={`admin-dex-mode-${m}`}
              >
                {m.toUpperCase()}
              </Button>
            ))}
          </div>

          {/* Custom token address */}
          <div className="mb-4">
            <Label className="text-xs">$DEEPOTUS token mint address (Solana)</Label>
            <div className="flex gap-2 mt-1">
              <Input
                value={dexCustomAddr}
                onChange={(e) => setDexCustomAddr(e.target.value.trim())}
                placeholder="e.g. 4k3D...mhAZ"
                className="font-mono"
                data-testid="admin-dex-custom-input"
              />
              <Button
                variant="outline"
                onClick={() => setDexMode("custom")}
                disabled={!dexCustomAddr.trim()}
                className="rounded-[var(--btn-radius)]"
                data-testid="admin-dex-custom-save"
              >
                Save & activate
              </Button>
            </div>
          </div>

          {/* Status panel */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
            <div className="rounded-md border border-border bg-background p-3">
              <div className="text-muted-foreground text-[10px] uppercase">price</div>
              <div className="text-foreground mt-0.5">${state?.dex_last_price_usd?.toFixed(8) || "—"}</div>
            </div>
            <div className="rounded-md border border-border bg-background p-3">
              <div className="text-muted-foreground text-[10px] uppercase">buys h24</div>
              <div className="text-foreground mt-0.5">{state?.dex_last_h24_buys?.toLocaleString() || "—"}</div>
            </div>
            <div className="rounded-md border border-border bg-background p-3">
              <div className="text-muted-foreground text-[10px] uppercase">volume h24</div>
              <div className="text-foreground mt-0.5">${state?.dex_last_h24_volume_usd?.toLocaleString() || "—"}</div>
            </div>
            <div className="rounded-md border border-border bg-background p-3">
              <div className="text-muted-foreground text-[10px] uppercase">carry</div>
              <div className="text-foreground mt-0.5">{Math.round(state?.dex_carry_tokens || 0).toLocaleString()}</div>
            </div>
          </div>

          {state?.dex_error && (
            <div className="mt-3 rounded-md border border-red-500/30 bg-red-500/5 p-2 font-mono text-[11px] text-red-400">
              last error: {state.dex_error}
            </div>
          )}

          {/* Action row */}
          <div className="mt-4 flex items-center gap-2 flex-wrap">
            <Button
              onClick={forcePoll}
              size="sm"
              disabled={dexPollBusy || state?.dex_mode === "off"}
              className="rounded-[var(--btn-radius)]"
              data-testid="admin-dex-force-poll"
            >
              <Play size={14} className="mr-1" /> {dexPollBusy ? "Polling…" : "Force poll now"}
            </Button>
            <a
              href={
                state?.dex_mode === "demo"
                  ? `https://dexscreener.com/solana/${state?.dex_demo_token_address || ""}`
                  : state?.dex_token_address
                  ? `https://dexscreener.com/solana/${state.dex_token_address}`
                  : "https://dexscreener.com/solana"
              }
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              data-testid="admin-dex-external-link"
            >
              View on DexScreener <ExternalLink size={12} />
            </a>
            {state?.dex_last_poll_at && (
              <span className="ml-auto font-mono text-[10px] text-muted-foreground">
                last poll: {new Date(state.dex_last_poll_at).toLocaleTimeString()}
              </span>
            )}
          </div>

          {dexLastPoll && !dexLastPoll.skipped && (
            <div className="mt-3 rounded-md border border-border bg-background p-3 font-mono text-[11px] text-foreground/80">
              <div className="text-muted-foreground text-[10px] uppercase mb-1">last force-poll result</div>
              <div>
                {dexLastPoll.pair} · Δbuys={dexLastPoll.delta_buys} · Δvol=${(dexLastPoll.delta_vol_usd || 0).toFixed(2)} · ticks={dexLastPoll.ticks_applied}
              </div>
            </div>
          )}
        </section>

        {/* Helius Per-Trade Indexer (extracted to TSX, Sprint 6 split) */}
        <HeliusSection
          api={API}
          headers={headers}
          vaultDexMode={state?.dex_mode}
          onChanged={load}
        />

        {/* Classified Vault Seal Status (Sprint 11 — pre-launch gate) */}
        <SealStatusSection api={API} headers={headers} />



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
