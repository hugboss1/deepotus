/**
 * WhaleWatcherTab — admin surface for the Brain Connect Whale Watcher
 * (Sprint 15.3, follows Sprint 15.2 backend).
 *
 * Three sections:
 *   1. **Stats card** — 24h aggregates by tier + queue counters.
 *   2. **Simulate form** — inject a synthetic alert (demo-mode E2E test).
 *   3. **Recent alerts list** — auto-refreshing audit feed.
 *
 * The component is intentionally compact so it can sit beside the
 * Propaganda Engine tabs without inflating the parent file.
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RadioTower,
  Search,
  Send,
  Shield,
  ShieldAlert,
  Wallet,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getAdminToken } from "@/lib/adminAuth";
import { logger } from "@/lib/logger";

const API: string = process.env.REACT_APP_BACKEND_URL || "";
const REFRESH_MS = 8_000;

interface WhaleAlert {
  _id: string;
  buyer: string;
  buyer_short?: string | null;
  amount_sol: number;
  tier: "T1" | "T2" | "T3" | null;
  status:
    | "detected"
    | "analyzing"
    | "propaganda_proposed"
    | "notified"
    | "skipped"
    | "error";
  source?: string | null;
  tx_signature?: string | null;
  ts: string | Date;
  propaganda_queue_id?: string | null;
  skip_reason?: string | null;
  error?: string | null;
}

interface TierStats {
  n: number;
  sol_sum: number;
}

interface StatsResponse {
  by_tier_24h: Record<string, TierStats>;
  pending: number;
  errored: number;
}

const TIER_COLOR: Record<string, string> = {
  T1: "text-[#18C964]",
  T2: "text-[#F59E0B]",
  T3: "text-[#FF4D4D]",
};

const STATUS_COLOR: Record<WhaleAlert["status"], string> = {
  detected: "text-[#22D3EE]",
  analyzing: "text-[#22D3EE]",
  propaganda_proposed: "text-[#18C964]",
  notified: "text-[#18C964]",
  skipped: "text-muted-foreground",
  error: "text-[#FF4D4D]",
};

function authHeaders() {
  const t = getAdminToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

function fmt(d: string | Date | undefined | null): string {
  if (!d) return "—";
  try {
    return new Date(d).toLocaleTimeString();
  } catch {
    return String(d);
  }
}

export default function WhaleWatcherTab(): JSX.Element {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [alerts, setAlerts] = useState<WhaleAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [tierFilter, setTierFilter] = useState<string>("all");

  // Simulate form state
  const [simAmount, setSimAmount] = useState<string>("12");
  const [simBuyer, setSimBuyer] = useState<string>("");
  const [simBusy, setSimBusy] = useState<boolean>(false);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { limit: 50 };
      if (statusFilter !== "all") params.status = statusFilter;
      if (tierFilter !== "all") params.tier = tierFilter;
      const { data } = await axios.get<{ items: WhaleAlert[]; count: number }>(
        `${API}/api/admin/whale-watcher/alerts`,
        { params, headers: authHeaders() },
      );
      setAlerts(data.items || []);
    } catch (err) {
      logger.error(err);
      toast.error("Failed to load whale alerts");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, tierFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const { data } = await axios.get<StatsResponse>(
        `${API}/api/admin/whale-watcher/stats`,
        { headers: authHeaders() },
      );
      setStats(data);
    } catch (err) {
      logger.error(err);
    }
  }, []);

  useEffect(() => {
    void fetchAlerts();
    void fetchStats();
  }, [fetchAlerts, fetchStats]);

  // Auto-refresh both panels — keeps the burst absorber visible in real time.
  useEffect(() => {
    const id = window.setInterval(() => {
      void fetchAlerts();
      void fetchStats();
    }, REFRESH_MS);
    return () => window.clearInterval(id);
  }, [fetchAlerts, fetchStats]);

  const submitSimulate = useCallback(async () => {
    const amount = parseFloat(simAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      toast.error("Enter a positive amount in SOL");
      return;
    }
    setSimBusy(true);
    try {
      const body: Record<string, unknown> = { amount_sol: amount };
      const buyerTrim = simBuyer.trim();
      if (buyerTrim.length >= 4) body.buyer = buyerTrim;
      const { data } = await axios.post<{
        ok: boolean;
        duplicate: boolean;
        alert: WhaleAlert;
      }>(`${API}/api/admin/whale-watcher/simulate`, body, {
        headers: authHeaders(),
      });
      if (data.duplicate) {
        toast.message("Already enqueued (idempotent)", {
          description: "This tx_signature is already in the queue.",
        });
      } else {
        toast.success("Whale alert enqueued", {
          description: `tier=${data.alert.tier} · ${amount} SOL`,
        });
      }
      // Reset form for the next test
      setSimAmount(String(amount));
      setSimBuyer("");
      void fetchAlerts();
      void fetchStats();
    } catch (err) {
      logger.error(err);
      // eslint-disable-next-line
      const detail = (err as any)?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Simulate failed");
    } finally {
      setSimBusy(false);
    }
  }, [simAmount, simBuyer, fetchAlerts, fetchStats]);

  const tiers = useMemo(() => {
    const t = stats?.by_tier_24h || {};
    return [
      {
        key: "T1",
        label: "T1 · 5–15 SOL",
        n: t.T1?.n || 0,
        sol: t.T1?.sol_sum || 0,
      },
      {
        key: "T2",
        label: "T2 · 15–50 SOL",
        n: t.T2?.n || 0,
        sol: t.T2?.sol_sum || 0,
      },
      {
        key: "T3",
        label: "T3 · 50+ SOL",
        n: t.T3?.n || 0,
        sol: t.T3?.sol_sum || 0,
      },
    ];
  }, [stats]);

  return (
    <div className="space-y-6" data-testid="whale-watcher-tab">
      {/* Header explainer */}
      <div className="rounded-md border border-[#22D3EE]/40 bg-[#22D3EE]/5 p-3 text-xs text-[#22D3EE] font-mono inline-flex items-center gap-2">
        <RadioTower size={14} />
        Brain Connect — observation only. Reads on-chain BUYs ≥ 5 SOL via
        Helius, classifies them in 3 tiers, and feeds the Propaganda queue.
        <strong className="ml-1">Never holds a private key.</strong>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {tiers.map((t) => (
          <div
            key={t.key}
            className="rounded-md border border-border bg-background/40 p-3"
            data-testid={`whale-tier-stat-${t.key}`}
          >
            <div
              className={`text-[10px] uppercase tracking-widest ${
                TIER_COLOR[t.key]
              }`}
            >
              {t.label} · 24h
            </div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-mono font-semibold">{t.n}</span>
              <span className="text-[11px] text-muted-foreground">
                · {t.sol.toFixed(2)} SOL
              </span>
            </div>
          </div>
        ))}
        <div className="rounded-md border border-border bg-background/40 p-3">
          <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
            Queue
          </div>
          <div className="mt-1 flex items-center gap-3">
            <div className="flex flex-col">
              <span className="text-[10px] text-muted-foreground">pending</span>
              <span className="text-xl font-mono font-semibold">
                {stats?.pending ?? "—"}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-muted-foreground">errored</span>
              <span
                className={`text-xl font-mono font-semibold ${
                  (stats?.errored ?? 0) > 0
                    ? "text-[#FF4D4D]"
                    : "text-foreground"
                }`}
              >
                {stats?.errored ?? "—"}
              </span>
            </div>
          </div>
        </div>
        <div className="rounded-md border border-border bg-background/40 p-3 flex items-center justify-center gap-2 text-[11px] text-muted-foreground font-mono">
          <Activity size={12} className="text-[#18C964]" />
          tick: every 5s
        </div>
      </div>

      {/* Simulate card */}
      <div
        className="rounded-md border border-[#F59E0B]/40 bg-[#F59E0B]/5 p-4 space-y-3"
        data-testid="whale-simulate-card"
      >
        <div className="flex items-center gap-2 text-[#F59E0B] font-mono text-xs uppercase tracking-widest">
          <ShieldAlert size={14} />
          Simulate a whale alert (admin-only · demo-mode E2E)
        </div>
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
          <div className="md:col-span-3 space-y-1">
            <Label htmlFor="sim-amount" className="text-[11px]">
              Amount (SOL)
            </Label>
            <Input
              id="sim-amount"
              type="number"
              min="0.1"
              step="0.5"
              value={simAmount}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setSimAmount(e.target.value)}
              disabled={simBusy}
              data-testid="whale-sim-amount"
            />
          </div>
          <div className="md:col-span-7 space-y-1">
            <Label htmlFor="sim-buyer" className="text-[11px]">
              Buyer pubkey (optional · auto-generated if blank)
            </Label>
            <Input
              id="sim-buyer"
              placeholder="7gXkHxJzwy5oQGNh4tPmWqRsBnYxL8KvCfDz3dT2kQ4u"
              value={simBuyer}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setSimBuyer(e.target.value)}
              disabled={simBusy}
              spellCheck={false}
              autoCapitalize="off"
              autoCorrect="off"
              data-testid="whale-sim-buyer"
            />
          </div>
          <div className="md:col-span-2">
            <Button
              onClick={submitSimulate}
              disabled={simBusy}
              className="w-full rounded-[var(--btn-radius)] bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
              data-testid="whale-sim-submit"
            >
              {simBusy ? (
                <Loader2 size={14} className="mr-1 animate-spin" />
              ) : (
                <Send size={14} className="mr-1" />
              )}
              Enqueue
            </Button>
          </div>
        </div>
        <div className="text-[10px] text-muted-foreground font-mono">
          → On enqueue, the APScheduler tick will pick it up within 5 s and
          propose a Propaganda queue item using the matching tier template.
          Status transitions: <code>detected → analyzing → propaganda_proposed</code>.
        </div>
      </div>

      {/* Filters + alerts list */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Search size={12} className="text-muted-foreground" />
          <Label className="text-[11px] text-muted-foreground">Status</Label>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger
              className="w-[200px] h-8 text-xs"
              data-testid="whale-filter-status"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="detected">detected</SelectItem>
              <SelectItem value="analyzing">analyzing</SelectItem>
              <SelectItem value="propaganda_proposed">
                propaganda_proposed
              </SelectItem>
              <SelectItem value="notified">notified</SelectItem>
              <SelectItem value="skipped">skipped</SelectItem>
              <SelectItem value="error">error</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Label className="text-[11px] text-muted-foreground">Tier</Label>
          <Select value={tierFilter} onValueChange={setTierFilter}>
            <SelectTrigger
              className="w-[120px] h-8 text-xs"
              data-testid="whale-filter-tier"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="T1">T1</SelectItem>
              <SelectItem value="T2">T2</SelectItem>
              <SelectItem value="T3">T3</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button
          onClick={() => {
            void fetchAlerts();
            void fetchStats();
          }}
          variant="outline"
          size="sm"
          disabled={loading}
          className="ml-auto rounded-[var(--btn-radius)]"
          data-testid="whale-refresh"
        >
          {loading ? (
            <Loader2 size={12} className="mr-1 animate-spin" />
          ) : (
            <Activity size={12} className="mr-1" />
          )}
          Refresh
        </Button>
      </div>

      {(() => {
        if (loading && alerts.length === 0) {
          return (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin" size={20} />
            </div>
          );
        }
        if (alerts.length === 0) {
          return (
            <div className="text-center text-sm text-muted-foreground py-12">
              No alerts match these filters.
            </div>
          );
        }
        return (
          <ScrollArea className="h-[480px] pr-2">
            <ul className="space-y-1.5 font-mono text-[12px]">
              {alerts.map((a) => (
                <li
                  key={a._id}
                  className="flex items-start gap-3 rounded border border-border/60 bg-background/30 px-3 py-1.5"
                  data-testid={`whale-row-${a._id}`}
                >
                  <Wallet
                    size={11}
                    className={`mt-1 ${TIER_COLOR[a.tier || "T1"]}`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {a.tier && (
                        <Badge
                          variant="outline"
                          className={`${TIER_COLOR[a.tier]} border-current`}
                        >
                          {a.tier}
                        </Badge>
                      )}
                      <span className="text-foreground/90 font-semibold">
                        {a.amount_sol.toFixed(2)} SOL
                      </span>
                      <span
                        className={`uppercase tracking-widest text-[10px] ${
                          STATUS_COLOR[a.status]
                        }`}
                      >
                        {a.status === "propaganda_proposed" && (
                          <CheckCircle2 size={10} className="inline mr-1" />
                        )}
                        {a.status === "error" && (
                          <AlertTriangle size={10} className="inline mr-1" />
                        )}
                        {a.status}
                      </span>
                      {a.source && (
                        <span className="text-muted-foreground text-[10px]">
                          src: {a.source}
                        </span>
                      )}
                    </div>
                    <div className="text-muted-foreground text-[10px] mt-0.5 truncate">
                      buyer: {a.buyer || a.buyer_short || "—"}
                      {a.tx_signature && (
                        <>
                          {" · "}
                          tx: {a.tx_signature.slice(0, 18)}
                          {a.tx_signature.length > 18 && "…"}
                        </>
                      )}
                      {a.skip_reason && (
                        <span className="text-[#F59E0B] ml-1">
                          · {a.skip_reason}
                        </span>
                      )}
                      {a.error && (
                        <span className="text-[#FF4D4D] ml-1">
                          · {a.error}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="text-muted-foreground text-[10px] shrink-0">
                    {fmt(a.ts)}
                  </span>
                </li>
              ))}
            </ul>
          </ScrollArea>
        );
      })()}

      <div className="flex items-center gap-2 text-[10px] text-muted-foreground font-mono">
        <Shield size={11} />
        Propaganda dispatch is gated by the Sleeper Cell mode (Infiltration
        Brain). Whales enqueued during Sleeper-active phases will be marked
        <code className="mx-1">skipped:propaganda:sleeper_cell_active</code>—
        the audit trail is preserved.
      </div>
    </div>
  );
}
