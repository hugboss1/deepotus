/**
 * GiveawayExtractionCard — admin UI for the Sprint 19+ extraction
 * pipeline (Cabinet → CabinetTab in /admin/propaganda).
 *
 * Surfaces three operator actions in one card:
 *  1. **Inspect eligibility** — read-only roll-call of whitelisted
 *     candidates with their wallet linkage state. Tells the operator
 *     who still needs a manual wallet override before extraction.
 *  2. **Preview** — dry-run an extraction against the live Solana
 *     blockhash. Renders the would-be winners + holdings audit but
 *     does NOT lock the draw_date (multiple previews allowed).
 *  3. **Extract + Announce** — real run that persists a snapshot and
 *     blocks the draw_date. From the snapshot the operator can fire
 *     the propaganda announcement on X + Telegram.
 *
 * Pre-mint awareness: the card highlights when the system is running
 * in PRE-MINT mode (no on-chain check, every candidate verified by
 * fallback) so the operator never confuses "5/5 verified" with "5
 * wallets actually hold $30 of $DEEP".
 */

import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Gift,
  Loader2,
  Megaphone,
  Play,
  RefreshCcw,
  Search,
  ShieldOff,
  Sparkles,
  Trash2,
  Users,
  Wallet,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getAdminToken } from "@/lib/adminAuth";
import { logger } from "@/lib/logger";

const API: string = (import.meta as unknown as { env: { REACT_APP_BACKEND_URL?: string } }).env?.REACT_APP_BACKEND_URL
  || (process as unknown as { env: { REACT_APP_BACKEND_URL?: string } }).env?.REACT_APP_BACKEND_URL
  || "";

function authHeaders(): Record<string, string> {
  const t = getAdminToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

function handleError(err: unknown, fallback: string): void {
  // eslint-disable-next-line
  const errAny = err as any;
  const msg = errAny?.response?.data?.detail?.error
    || errAny?.response?.data?.detail
    || errAny?.message
    || fallback;
  logger.error("[giveaway-extraction]", err);
  toast.error(typeof msg === "string" ? msg : fallback);
}

// =====================================================================
// Types — mirror the backend response shapes (lib/giveaway router).
// =====================================================================
interface EligibleRow {
  email: string;
  x_handle: string;
  wallet_address: string | null;
  level: number;
  verified_human: boolean;
  created_at: string | null;
}

interface WinnerRow {
  x_handle: string;
  email: string | null;
  wallet: string | null;
  wallet_short: string;
  level: number;
  status: string;
  holding_tokens: number;
  holding_usd: number;
}

interface Snapshot {
  snapshot_id: string;
  kind: "preview" | "extraction";
  draw_date_iso: string;
  token_mint: string | null;
  pre_mint: boolean;
  pool_sol: number;
  per_winner_sol: number;
  winners_count_target: number;
  min_holding_usd: number;
  eligible_count: number;
  verified_count: number;
  winners: WinnerRow[];
  details: WinnerRow[];
  price_usd: number | null;
  seed: {
    blockhash: string;
    slot: number;
    captured_at: string;
    fingerprint: string;
  } | null;
  errors: string[];
  created_at: string | null;
  cancelled_at: string | null;
  announced_queue_item_id: string | null;
}

interface EligibleResponse {
  items: EligibleRow[];
  count: number;
  with_wallet: number;
  without_wallet: number;
}

// =====================================================================
// Component
// =====================================================================
export function GiveawayExtractionCard(): React.ReactElement {
  // Form state
  const [drawDate, setDrawDate] = useState<string>("2026-05-20T18:00:00Z");
  const [poolSol, setPoolSol] = useState<string>("5");
  const [winnersCount, setWinnersCount] = useState<string>("2");
  const [minUsd, setMinUsd] = useState<string>("30");

  // Data state
  const [eligible, setEligible] = useState<EligibleResponse | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [lastSnapshot, setLastSnapshot] = useState<Snapshot | null>(null);
  const [loadingEligible, setLoadingEligible] = useState<boolean>(false);
  const [loadingPreview, setLoadingPreview] = useState<boolean>(false);
  const [loadingExtract, setLoadingExtract] = useState<boolean>(false);
  const [announcing, setAnnouncing] = useState<string | null>(null);

  const loadEligible = useCallback(async (): Promise<void> => {
    setLoadingEligible(true);
    try {
      const { data } = await axios.get<EligibleResponse>(
        `${API}/api/admin/giveaway/eligible`,
        { headers: authHeaders() },
      );
      setEligible(data);
    } catch (err) {
      handleError(err, "Eligibility query failed");
    } finally {
      setLoadingEligible(false);
    }
  }, []);

  const loadSnapshots = useCallback(async (): Promise<void> => {
    try {
      const { data } = await axios.get<{ items: Snapshot[] }>(
        `${API}/api/admin/giveaway/snapshots?limit=20`,
        { headers: authHeaders() },
      );
      setSnapshots(data?.items ?? []);
    } catch (err) {
      handleError(err, "Snapshots list failed");
    }
  }, []);

  useEffect(() => {
    void loadEligible();
    void loadSnapshots();
  }, [loadEligible, loadSnapshots]);

  // ---- Actions ----
  const runPreview = async (): Promise<void> => {
    setLoadingPreview(true);
    setLastSnapshot(null);
    try {
      const { data } = await axios.post<{ ok: boolean; snapshot: Snapshot }>(
        `${API}/api/admin/giveaway/preview`,
        {
          draw_date_iso: drawDate.trim(),
          pool_sol: Number(poolSol),
          winners_count: Number(winnersCount),
          min_holding_usd: Number(minUsd),
        },
        { headers: authHeaders() },
      );
      setLastSnapshot(data.snapshot);
      if (data.snapshot.pre_mint) {
        toast.warning("PRE-MINT mode — on-chain holdings check skipped.");
      } else {
        toast.success(
          `Preview: ${data.snapshot.winners.length} winners from ${data.snapshot.verified_count} verified.`,
        );
      }
      await loadSnapshots();
    } catch (err) {
      handleError(err, "Preview failed");
    } finally {
      setLoadingPreview(false);
    }
  };

  const runExtract = async (): Promise<void> => {
    if (!window.confirm(
      `Lock extraction for ${drawDate}? This blocks the draw_date until cancelled.`,
    )) {
      return;
    }
    setLoadingExtract(true);
    try {
      const { data } = await axios.post<{ ok: boolean; snapshot: Snapshot }>(
        `${API}/api/admin/giveaway/extract`,
        {
          draw_date_iso: drawDate.trim(),
          pool_sol: Number(poolSol),
          winners_count: Number(winnersCount),
          min_holding_usd: Number(minUsd),
        },
        { headers: authHeaders() },
      );
      setLastSnapshot(data.snapshot);
      toast.success(`Extraction locked — ${data.snapshot.winners.length} winners selected.`);
      await loadSnapshots();
    } catch (err: unknown) {
      // eslint-disable-next-line
      const errAny = err as any;
      const status = errAny?.response?.status;
      const detail = errAny?.response?.data?.detail;
      if (status === 409 && detail?.error === "duplicate_active_extraction") {
        toast.warning("An extraction already exists for this draw_date. Cancel it first.");
        await loadSnapshots();
      } else {
        handleError(err, "Extraction failed");
      }
    } finally {
      setLoadingExtract(false);
    }
  };

  const announce = async (id: string): Promise<void> => {
    setAnnouncing(id);
    try {
      const { data } = await axios.post<{
        ok: boolean;
        queue_item_id: string | null;
        announce_error: string | null;
      }>(
        `${API}/api/admin/giveaway/snapshots/${id}/announce`,
        { language: "en" },
        { headers: authHeaders() },
      );
      if (data.ok && data.queue_item_id) {
        toast.success("Announcement queued for X + Telegram approval.");
      } else {
        toast.warning(`Announce: ${data.announce_error || "unknown error"}`);
      }
      await loadSnapshots();
    } catch (err) {
      handleError(err, "Announce failed");
    } finally {
      setAnnouncing(null);
    }
  };

  const cancel = async (id: string): Promise<void> => {
    if (!window.confirm("Cancel this snapshot? It will be hidden from list and the draw_date slot freed.")) {
      return;
    }
    try {
      await axios.post(
        `${API}/api/admin/giveaway/snapshots/${id}/cancel`,
        {},
        { headers: authHeaders() },
      );
      toast.success("Snapshot cancelled.");
      await loadSnapshots();
    } catch (err) {
      handleError(err, "Cancel failed");
    }
  };

  // ---- Render ----
  return (
    <Card data-testid="cabinet-giveaway-extraction-card">
      <CardHeader>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Gift size={16} className="text-[#F59E0B]" />
              Giveaway Extraction
              <Badge variant="outline" data-testid="giveaway-extraction-badge">
                CABINET DRAW
              </Badge>
            </CardTitle>
            <CardDescription>
              Run the May 20 (or future) public draw: eligibility query → Helius
              holdings check → provably-fair Solana slot RNG → 2 winners →
              automated Prophet announcement.
            </CardDescription>
          </div>
          {eligible && (
            <div className="text-right text-xs font-mono space-y-0.5">
              <div className="text-foreground/55 flex items-center gap-1 justify-end">
                <Users size={12} /> {eligible.count} eligible
              </div>
              <div className="text-[10px] text-foreground/45">
                <Wallet size={10} className="inline mr-1" />
                {eligible.with_wallet} linked · {eligible.without_wallet} unlinked
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* ---- Eligibility roll-call ---- */}
        <div className="rounded-md border border-border bg-muted/20 p-4 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="text-xs uppercase tracking-wider text-muted-foreground font-mono flex items-center gap-2">
              <Search size={12} /> Eligibility roll-call
              {loadingEligible && <Loader2 size={12} className="animate-spin" />}
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={(): void => {
                void loadEligible();
              }}
              data-testid="giveaway-eligible-refresh"
            >
              <RefreshCcw size={12} className="mr-1.5" /> Refresh
            </Button>
          </div>
          {!eligible || eligible.count === 0 ? (
            <div className="text-xs text-muted-foreground py-3 text-center">
              No eligible candidates yet (need at least one row in clearance_levels with x_handle).
            </div>
          ) : (
            <ul className="space-y-1 max-h-44 overflow-auto pr-2" data-testid="giveaway-eligible-list">
              {eligible.items.slice(0, 50).map((r) => (
                <li
                  key={r.email}
                  className="flex items-center justify-between gap-2 text-xs font-mono py-1 border-b border-border/30"
                  data-testid={`giveaway-eligible-${r.x_handle}`}
                >
                  <span className="text-[#22D3EE]">@{r.x_handle}</span>
                  <span className="text-foreground/55 truncate flex-1 mx-2">{r.email}</span>
                  {r.wallet_address ? (
                    <Badge variant="secondary" className="text-[9px]">
                      <Wallet size={9} className="mr-0.5" /> linked
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-[9px] border-[#F59E0B]/50 text-[#F59E0B]">
                      <ShieldOff size={9} className="mr-0.5" /> no wallet
                    </Badge>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* ---- Extraction form ---- */}
        <div className="rounded-md border border-border bg-muted/20 p-4 space-y-3">
          <div className="text-xs uppercase tracking-wider text-muted-foreground font-mono">
            Extraction parameters
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <Label htmlFor="giv-draw" className="text-xs">
                Draw date (ISO UTC)
              </Label>
              <Input
                id="giv-draw"
                value={drawDate}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void => setDrawDate(e.target.value)}
                className="font-mono text-xs"
                data-testid="giveaway-input-draw"
              />
            </div>
            <div>
              <Label htmlFor="giv-pool" className="text-xs">
                Pool (SOL)
              </Label>
              <Input
                id="giv-pool"
                type="number"
                min="0"
                step="0.1"
                value={poolSol}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void => setPoolSol(e.target.value)}
                data-testid="giveaway-input-pool"
              />
            </div>
            <div>
              <Label htmlFor="giv-count" className="text-xs">
                Winners
              </Label>
              <Input
                id="giv-count"
                type="number"
                min="1"
                max="20"
                value={winnersCount}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void => setWinnersCount(e.target.value)}
                data-testid="giveaway-input-count"
              />
            </div>
            <div>
              <Label htmlFor="giv-usd" className="text-xs">
                Min hold (USD)
              </Label>
              <Input
                id="giv-usd"
                type="number"
                min="0"
                step="1"
                value={minUsd}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void => setMinUsd(e.target.value)}
                data-testid="giveaway-input-usd"
              />
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap pt-1">
            <Button
              variant="secondary"
              onClick={(): void => {
                void runPreview();
              }}
              disabled={loadingPreview || loadingExtract}
              data-testid="giveaway-preview-btn"
            >
              {loadingPreview ? (
                <>
                  <Loader2 size={14} className="mr-1.5 animate-spin" /> Previewing…
                </>
              ) : (
                <>
                  <Play size={14} className="mr-1.5" /> Preview (dry-run)
                </>
              )}
            </Button>
            <Button
              onClick={(): void => {
                void runExtract();
              }}
              disabled={loadingExtract || loadingPreview}
              data-testid="giveaway-extract-btn"
            >
              {loadingExtract ? (
                <>
                  <Loader2 size={14} className="mr-1.5 animate-spin" /> Extracting…
                </>
              ) : (
                <>
                  <Sparkles size={14} className="mr-1.5" /> Run extraction (lock)
                </>
              )}
            </Button>
          </div>
        </div>

        {/* ---- Last snapshot result ---- */}
        {lastSnapshot && (
          <div
            className="rounded-md border border-[#F59E0B]/45 bg-[#F59E0B]/[0.04] p-4 space-y-3"
            data-testid="giveaway-last-snapshot"
          >
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="text-xs uppercase tracking-wider text-[#F59E0B] font-mono">
                {lastSnapshot.kind === "preview" ? "Preview" : "Extraction"} ·{" "}
                <span className="text-foreground/70">{lastSnapshot.snapshot_id.slice(0, 8)}…</span>
                {lastSnapshot.pre_mint && (
                  <Badge variant="outline" className="ml-2 text-[9px] border-[#FF3B3B]/50 text-[#FF3B3B]">
                    PRE-MINT
                  </Badge>
                )}
              </div>
              <div className="text-[10px] font-mono text-foreground/55">
                eligible {lastSnapshot.eligible_count} · verified {lastSnapshot.verified_count} ·{" "}
                pool {lastSnapshot.pool_sol} SOL → {lastSnapshot.per_winner_sol} SOL each
              </div>
            </div>
            {lastSnapshot.seed && (
              <div className="text-[10px] font-mono text-foreground/45 break-all">
                <CheckCircle2 size={10} className="inline mr-1 text-[#33FF66]" />
                Solana slot <span className="text-foreground/70">{lastSnapshot.seed.slot}</span> · seed{" "}
                <span className="text-foreground/70">{lastSnapshot.seed.fingerprint.slice(0, 16)}…</span>
              </div>
            )}
            <ul className="space-y-1" data-testid="giveaway-snapshot-winners">
              {lastSnapshot.winners.map((w) => (
                <li
                  key={w.x_handle}
                  className="flex items-center justify-between gap-2 text-xs font-mono py-1 px-2 rounded bg-background"
                  data-testid={`giveaway-winner-${w.x_handle}`}
                >
                  <span className="text-[#33FF66] font-semibold">@{w.x_handle}</span>
                  <span className="text-foreground/55">{w.wallet_short}</span>
                  <Badge variant="secondary" className="text-[9px]">
                    {w.status === "verified"
                      ? `${w.holding_usd.toFixed(2)} USD`
                      : w.status}
                  </Badge>
                </li>
              ))}
            </ul>
            {lastSnapshot.errors.length > 0 && (
              <div className="text-[10px] text-[#F59E0B] flex items-start gap-1">
                <AlertTriangle size={10} className="mt-0.5 shrink-0" />
                <span>{lastSnapshot.errors.join(" · ")}</span>
              </div>
            )}
          </div>
        )}

        {/* ---- Snapshots history ---- */}
        <div className="rounded-md border border-border bg-muted/30 p-3">
          <div className="text-xs uppercase tracking-wider text-muted-foreground font-mono mb-2">
            Snapshots history
          </div>
          {snapshots.length === 0 ? (
            <div className="text-xs text-muted-foreground py-3 text-center">No snapshots yet.</div>
          ) : (
            <ul className="space-y-2 max-h-80 overflow-auto pr-2" data-testid="giveaway-snapshots-list">
              {snapshots.map((s) => {
                const isCancelled = s.cancelled_at !== null;
                return (
                  <li
                    key={s.snapshot_id}
                    className={`rounded border border-border bg-background px-3 py-2 ${isCancelled ? "opacity-50" : ""}`}
                    data-testid={`giveaway-snapshot-${s.snapshot_id}`}
                  >
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2 font-mono text-xs">
                        <span className={s.kind === "extraction" ? "text-[#F59E0B] font-semibold" : "text-foreground/55"}>
                          {s.kind.toUpperCase()}
                        </span>
                        <span className="text-foreground/45">{s.snapshot_id.slice(0, 8)}…</span>
                        <span className="text-foreground/55">{s.draw_date_iso.slice(0, 10)}</span>
                        {s.pre_mint && (
                          <Badge variant="outline" className="text-[9px] border-[#FF3B3B]/50 text-[#FF3B3B]">
                            PRE-MINT
                          </Badge>
                        )}
                        {isCancelled && (
                          <Badge variant="destructive" className="text-[9px]">CANCELLED</Badge>
                        )}
                        {s.announced_queue_item_id && (
                          <Badge variant="secondary" className="text-[9px]">ANNOUNCED</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        {!isCancelled && s.kind === "extraction" && !s.announced_queue_item_id && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2 text-[10px]"
                            onClick={(): void => {
                              void announce(s.snapshot_id);
                            }}
                            disabled={announcing === s.snapshot_id}
                            data-testid={`giveaway-announce-${s.snapshot_id}`}
                          >
                            {announcing === s.snapshot_id ? (
                              <Loader2 size={11} className="animate-spin" />
                            ) : (
                              <>
                                <Megaphone size={11} className="mr-1" /> Announce
                              </>
                            )}
                          </Button>
                        )}
                        {s.announced_queue_item_id && (
                          <a
                            href="/propaganda"
                            className="text-[10px] font-mono text-[#22D3EE] hover:text-[#33FF66] inline-flex items-center gap-1 px-1.5"
                          >
                            queue <ExternalLink size={9} />
                          </a>
                        )}
                        {!isCancelled && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={(): void => {
                              void cancel(s.snapshot_id);
                            }}
                            data-testid={`giveaway-cancel-${s.snapshot_id}`}
                          >
                            <Trash2 size={11} />
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="mt-1 text-[10px] text-muted-foreground font-mono">
                      eligible {s.eligible_count} · verified {s.verified_count} ·{" "}
                      winners {s.winners.length}/{s.winners_count_target} ·{" "}
                      {s.pool_sol} SOL → {s.per_winner_sol} SOL/winner
                      {s.winners.length > 0 && (
                        <>
                          {" · "}
                          {s.winners.map((w) => `@${w.x_handle}`).join(", ")}
                        </>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
