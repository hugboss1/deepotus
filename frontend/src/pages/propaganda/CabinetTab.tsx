/**
 * Cabinet Expansion tab — Sprint 17.5.
 *
 * Two operator surfaces in one tab:
 *
 *   1. Welcome Signal — daily Cabinet recognition broadcast that cites
 *      the 5 most-recently accredited Agents who provided their X
 *      handle. Admin can toggle, tune the firing hour, and "Fire now"
 *      to bypass the daily-once gate for a preview.
 *
 *   2. Prophet Interaction Bot — hourly Lore-compliant replies to the
 *      same accredited follower pool. OFF by default; admin enables it
 *      once X creds are confirmed live in production. "Fire now" runs
 *      one tick (1-3 replies) immediately, with a dry-run flag for
 *      smoke tests that don't burn X API credits.
 *
 * Both surfaces hit the new endpoints under `/api/admin/propaganda/`
 * (welcome-signal + interaction-bot). PATCH calls require 2FA on the
 * backend; the shared `handleError` from the parent Propaganda page
 * already maps 403/TWOFA_REQUIRED to a friendly toast.
 */

import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Bot,
  CheckCircle2,
  ExternalLink,
  Flame,
  Loader2,
  RadioTower,
  Send,
  Sparkles,
  Trash2,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getAdminToken } from "@/lib/adminAuth";
import { logger } from "@/lib/logger";
import { GiveawayExtractionCard } from "./GiveawayExtractionCard";

const API: string = process.env.REACT_APP_BACKEND_URL || "";

function authHeaders() {
  const t = getAdminToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

function handleError(err: unknown, fallback: string): void {
  // eslint-disable-next-line
  const detail = (err as any)?.response?.data?.detail;
  // eslint-disable-next-line
  const status = (err as any)?.response?.status;
  if (status === 403 && detail?.code === "TWOFA_REQUIRED") {
    toast.error("2FA required", {
      description: "Enable 2FA from Admin → Security before flipping toggles.",
    });
    return;
  }
  toast.error(typeof detail === "string" ? detail : fallback);
  logger.error(err);
}

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------
interface WelcomeSignalCfg {
  enabled: boolean;
  hour_utc: number;
  min_handles: number;
  max_handles: number;
  last_fired_at: string | null;
  last_skip_reason: string | null;
  last_cited_handles: string[];
}

interface InteractionBotCfg {
  enabled: boolean;
  max_replies_per_hour: number;
  min_replies_per_hour: number;
  per_handle_cooldown_hours: number;
  last_fired_at: string | null;
  last_skip_reason: string | null;
  last_replies: Array<{
    handle: string;
    posted_tweet_id: string | null;
    dry_run: boolean;
    preview: string;
    at: string;
  }>;
  total_replies_lifetime: number;
}

interface RecentReply {
  id: string;
  agent_handle: string;
  source_tweet_id: string;
  rendered_reply: string;
  outcome: string;
  posted_tweet_id: string | null;
  error: string | null;
  posted_at: string;
}

// ---------------------------------------------------------------------
// Welcome Signal block
// ---------------------------------------------------------------------
function WelcomeSignalCard(): React.ReactElement {
  const [cfg, setCfg] = useState<WelcomeSignalCfg | null>(null);
  const [eligibleCount, setEligibleCount] = useState<number>(0);
  const [eligiblePreview, setEligiblePreview] = useState<
    Array<{ x_handle: string; email: string }>
  >([]);
  const [busy, setBusy] = useState<boolean>(false);
  const [firing, setFiring] = useState<boolean>(false);

  const load = useCallback(async () => {
    try {
      const { data } = await axios.get(
        `${API}/api/admin/propaganda/welcome-signal`,
        { headers: authHeaders() },
      );
      setCfg(data?.settings ?? null);
      setEligibleCount(Number(data?.eligible_count ?? 0));
      setEligiblePreview(data?.eligible_preview ?? []);
    } catch (err) {
      handleError(err, "Welcome Signal config load failed");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const patch = async (patchBody: Partial<WelcomeSignalCfg>): Promise<void> => {
    setBusy(true);
    try {
      const { data } = await axios.patch(
        `${API}/api/admin/propaganda/welcome-signal`,
        patchBody,
        { headers: authHeaders() },
      );
      setCfg(data?.settings ?? null);
      toast.success("Welcome Signal updated");
    } catch (err) {
      handleError(err, "Welcome Signal patch failed");
    } finally {
      setBusy(false);
    }
  };

  const fireNow = async (): Promise<void> => {
    setFiring(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/propaganda/welcome-signal/fire-now`,
        {},
        { headers: authHeaders() },
      );
      if (data?.fired) {
        toast.success(
          `Welcome Signal fired — ${(data?.cited_count ?? 0)} Agent(s) cited`,
        );
      } else {
        toast.warning(`Skipped — ${data?.reason ?? "unknown"}`);
      }
      await load();
    } catch (err) {
      handleError(err, "Welcome Signal fire failed");
    } finally {
      setFiring(false);
    }
  };

  if (!cfg) {
    return (
      <Card data-testid="cabinet-welcome-signal-card">
        <CardContent className="py-10 flex items-center justify-center text-muted-foreground">
          <Loader2 size={16} className="mr-2 animate-spin" /> Loading…
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="cabinet-welcome-signal-card">
      <CardHeader>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <CardTitle className="flex items-center gap-2">
              <RadioTower size={16} className="text-[#F59E0B]" />
              Welcome Signal
              <Badge
                variant={cfg.enabled ? "default" : "outline"}
                data-testid="cabinet-welcome-status-badge"
              >
                {cfg.enabled ? "ENABLED" : "PAUSED"}
              </Badge>
            </CardTitle>
            <CardDescription>
              Daily Cabinet recognition broadcast — cites the {cfg.max_handles}{" "}
              most-recently accredited Agents on X.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="ws-enabled" className="text-xs uppercase tracking-wider">
              Enabled
            </Label>
            <Switch
              id="ws-enabled"
              checked={cfg.enabled}
              disabled={busy}
              onCheckedChange={(v: boolean): void => {
                void patch({ enabled: v });
              }}
              data-testid="cabinet-welcome-toggle"
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="ws-hour" className="text-xs">
              Firing hour (UTC)
            </Label>
            <Input
              id="ws-hour"
              type="number"
              min={0}
              max={23}
              defaultValue={cfg.hour_utc}
              onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                const next = Math.max(0, Math.min(23, Number(e.target.value)));
                if (next !== cfg.hour_utc) void patch({ hour_utc: next });
              }}
              data-testid="cabinet-welcome-hour-input"
            />
          </div>
          <div>
            <Label htmlFor="ws-min" className="text-xs">
              Min handles to fire
            </Label>
            <Input
              id="ws-min"
              type="number"
              min={1}
              max={5}
              defaultValue={cfg.min_handles}
              onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                const next = Math.max(1, Math.min(5, Number(e.target.value)));
                if (next !== cfg.min_handles) void patch({ min_handles: next });
              }}
              data-testid="cabinet-welcome-min-input"
            />
          </div>
          <div>
            <Label htmlFor="ws-max" className="text-xs">
              Max handles cited
            </Label>
            <Input
              id="ws-max"
              type="number"
              min={1}
              max={5}
              defaultValue={cfg.max_handles}
              onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                const next = Math.max(1, Math.min(5, Number(e.target.value)));
                if (next !== cfg.max_handles) void patch({ max_handles: next });
              }}
              data-testid="cabinet-welcome-max-input"
            />
          </div>
        </div>

        <div className="rounded-md border border-border p-3 bg-muted/30 text-sm">
          <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-muted-foreground">
            <Users size={12} /> Eligible Agents queued
            <Badge variant="outline" data-testid="cabinet-welcome-eligible-count">
              {eligibleCount}
            </Badge>
          </div>
          {eligiblePreview.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-1.5" data-testid="cabinet-welcome-eligible-preview">
              {eligiblePreview.slice(0, cfg.max_handles).map((e) => (
                <Badge key={e.email} variant="secondary" className="font-mono">
                  @{e.x_handle}
                </Badge>
              ))}
            </div>
          ) : (
            <div className="mt-2 text-xs text-muted-foreground">
              No Agents with X handle waiting for the next broadcast.
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Button
            onClick={(): void => {
              void fireNow();
            }}
            disabled={firing}
            data-testid="cabinet-welcome-fire-now"
          >
            {firing ? (
              <>
                <Loader2 size={14} className="mr-1.5 animate-spin" /> Firing…
              </>
            ) : (
              <>
                <Send size={14} className="mr-1.5" /> Fire now (preview)
              </>
            )}
          </Button>
          <div className="text-xs text-muted-foreground font-mono">
            {cfg.last_fired_at
              ? `Last fired: ${new Date(cfg.last_fired_at).toLocaleString()}`
              : "Never fired."}
            {cfg.last_skip_reason && (
              <span className="ml-2 text-amber-500">
                · last skip: {cfg.last_skip_reason}
              </span>
            )}
          </div>
        </div>

        {cfg.last_cited_handles?.length > 0 && (
          <div className="text-xs text-muted-foreground">
            Last cited:{" "}
            {cfg.last_cited_handles.map((h) => `@${h}`).join(", ")}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------
// Interaction Bot block
// ---------------------------------------------------------------------
function InteractionBotCard(): React.ReactElement {
  const [cfg, setCfg] = useState<InteractionBotCfg | null>(null);
  const [recent, setRecent] = useState<RecentReply[]>([]);
  const [busy, setBusy] = useState<boolean>(false);
  const [firing, setFiring] = useState<boolean>(false);

  const load = useCallback(async () => {
    try {
      const { data } = await axios.get(
        `${API}/api/admin/propaganda/interaction-bot`,
        { headers: authHeaders() },
      );
      setCfg(data?.settings ?? null);
      setRecent(data?.recent_replies ?? []);
    } catch (err) {
      handleError(err, "Interaction Bot config load failed");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const patch = async (patchBody: Partial<InteractionBotCfg>): Promise<void> => {
    setBusy(true);
    try {
      const { data } = await axios.patch(
        `${API}/api/admin/propaganda/interaction-bot`,
        patchBody,
        { headers: authHeaders() },
      );
      setCfg(data?.settings ?? null);
      toast.success("Interaction Bot updated");
    } catch (err) {
      handleError(err, "Interaction Bot patch failed");
    } finally {
      setBusy(false);
    }
  };

  const fireNow = async (dryRun: boolean): Promise<void> => {
    setFiring(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/propaganda/interaction-bot/fire-now?dry_run=${dryRun}`,
        {},
        { headers: authHeaders() },
      );
      if (data?.fired) {
        toast.success(
          `Interaction Bot — ${data.fired} reply(ies)${dryRun ? " (DRY RUN)" : ""}`,
        );
      } else {
        toast.warning(`No replies fired — ${data?.reason ?? "unknown"}`);
      }
      await load();
    } catch (err) {
      handleError(err, "Interaction Bot fire failed");
    } finally {
      setFiring(false);
    }
  };

  if (!cfg) {
    return (
      <Card data-testid="cabinet-interaction-bot-card">
        <CardContent className="py-10 flex items-center justify-center text-muted-foreground">
          <Loader2 size={16} className="mr-2 animate-spin" /> Loading…
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="cabinet-interaction-bot-card">
      <CardHeader>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bot size={16} className="text-[#22D3EE]" />
              Prophet Interaction Bot
              <Badge
                variant={cfg.enabled ? "default" : "outline"}
                data-testid="cabinet-interaction-status-badge"
              >
                {cfg.enabled ? "ENABLED" : "PAUSED"}
              </Badge>
            </CardTitle>
            <CardDescription>
              Hourly Lore-compliant replies to accredited followers — signed{" "}
              <span className="font-mono">— ΔΣ</span>.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="ib-enabled" className="text-xs uppercase tracking-wider">
              Enabled
            </Label>
            <Switch
              id="ib-enabled"
              checked={cfg.enabled}
              disabled={busy}
              onCheckedChange={(v: boolean): void => {
                void patch({ enabled: v });
              }}
              data-testid="cabinet-interaction-toggle"
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="ib-min" className="text-xs">
              Min replies / hour
            </Label>
            <Input
              id="ib-min"
              type="number"
              min={0}
              max={5}
              defaultValue={cfg.min_replies_per_hour}
              onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                const next = Math.max(0, Math.min(5, Number(e.target.value)));
                if (next !== cfg.min_replies_per_hour)
                  void patch({ min_replies_per_hour: next });
              }}
              data-testid="cabinet-interaction-min-input"
            />
          </div>
          <div>
            <Label htmlFor="ib-max" className="text-xs">
              Max replies / hour
            </Label>
            <Input
              id="ib-max"
              type="number"
              min={1}
              max={5}
              defaultValue={cfg.max_replies_per_hour}
              onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                const next = Math.max(1, Math.min(5, Number(e.target.value)));
                if (next !== cfg.max_replies_per_hour)
                  void patch({ max_replies_per_hour: next });
              }}
              data-testid="cabinet-interaction-max-input"
            />
          </div>
          <div>
            <Label htmlFor="ib-cooldown" className="text-xs">
              Per-Agent cooldown (h)
            </Label>
            <Input
              id="ib-cooldown"
              type="number"
              min={1}
              max={168}
              defaultValue={cfg.per_handle_cooldown_hours}
              onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                const next = Math.max(1, Math.min(168, Number(e.target.value)));
                if (next !== cfg.per_handle_cooldown_hours)
                  void patch({ per_handle_cooldown_hours: next });
              }}
              data-testid="cabinet-interaction-cooldown-input"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Button
            onClick={(): void => {
              void fireNow(false);
            }}
            disabled={firing}
            data-testid="cabinet-interaction-fire-now"
          >
            {firing ? (
              <Loader2 size={14} className="mr-1.5 animate-spin" />
            ) : (
              <Send size={14} className="mr-1.5" />
            )}
            Fire now (live)
          </Button>
          <Button
            variant="outline"
            onClick={(): void => {
              void fireNow(true);
            }}
            disabled={firing}
            data-testid="cabinet-interaction-fire-dry"
          >
            <Sparkles size={14} className="mr-1.5" />
            Dry run
          </Button>
          <div className="text-xs text-muted-foreground font-mono">
            Lifetime replies: {cfg.total_replies_lifetime}
            {cfg.last_fired_at && (
              <span className="ml-2">
                · last:{" "}
                {new Date(cfg.last_fired_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>

        <div className="rounded-md border border-border p-3 bg-muted/30">
          <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-2">
            <CheckCircle2 size={12} /> Recent replies
          </div>
          {recent.length === 0 ? (
            <div className="text-xs text-muted-foreground">
              No replies recorded yet.
            </div>
          ) : (
            <ul
              className="space-y-2 max-h-72 overflow-auto pr-2"
              data-testid="cabinet-interaction-recent-list"
            >
              {recent.map((r) => (
                <li
                  key={r.id}
                  className="rounded border border-border bg-background px-3 py-2"
                >
                  <div className="flex items-center justify-between gap-2 text-xs font-mono">
                    <span className="text-foreground">@{r.agent_handle}</span>
                    <Badge
                      variant={
                        r.outcome === "sent"
                          ? "default"
                          : r.outcome === "dry_run"
                          ? "secondary"
                          : "destructive"
                      }
                      data-testid={`cabinet-interaction-outcome-${r.id}`}
                    >
                      {r.outcome}
                    </Badge>
                  </div>
                  <div className="mt-1 text-xs text-foreground/80 whitespace-pre-wrap">
                    {r.rendered_reply}
                  </div>
                  {r.error && (
                    <div className="mt-1 text-[10px] text-red-400">
                      err: {r.error}
                    </div>
                  )}
                  <div className="mt-1 text-[10px] text-muted-foreground">
                    {new Date(r.posted_at).toLocaleString()} · src{" "}
                    {r.source_tweet_id}
                    {r.posted_tweet_id && ` · posted ${r.posted_tweet_id}`}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------
// Operation Incinerator block (Sprint 17.6 — Burn disclosures)
// ---------------------------------------------------------------------
interface BurnRow {
  id: string;
  amount: number;
  tx_signature: string;
  tx_link: string;
  burned_at: string;
  source: string;
  note: string | null;
  redacted_at: string | null;
  redacted_by: string | null;
  created_at: string;
  created_by: string | null;
  queue_item_id: string | null;
}

interface BurnStats {
  initial_supply: number;
  total_burned: number;
  treasury_locked: number;
  team_locked: number;
  locked_total: number;
  locked_percent: number;
  effective_circulating: number;
  burn_count: number;
  burned_percent: number;
  latest_burn: { burned_at: string } | null;
}

function fmtBurnTokens(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString("en-US");
}

function IncineratorCard(): React.ReactElement {
  const [stats, setStats] = useState<BurnStats | null>(null);
  const [burns, setBurns] = useState<BurnRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Form state
  const [amount, setAmount] = useState<string>("");
  const [txSig, setTxSig] = useState<string>("");
  const [note, setNote] = useState<string>("");
  const [burnedAt, setBurnedAt] = useState<string>("");
  const [announce, setAnnounce] = useState<boolean>(true);
  const [language, setLanguage] = useState<"en" | "fr">("en");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/api/admin/burns`, {
        headers: authHeaders(),
      });
      setStats(data?.stats ?? null);
      setBurns(data?.items ?? []);
    } catch (err) {
      handleError(err, "Burn ledger load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const submit = async (): Promise<void> => {
    const parsedAmt = Number(amount);
    if (!Number.isFinite(parsedAmt) || parsedAmt <= 0) {
      toast.error("Amount must be a positive number.");
      return;
    }
    if (txSig.trim().length < 32) {
      toast.error("Transaction signature looks too short.");
      return;
    }
    setSubmitting(true);
    try {
      const body: Record<string, unknown> = {
        amount: parsedAmt,
        tx_signature: txSig.trim(),
        announce,
        language,
      };
      if (note.trim()) body.note = note.trim();
      if (burnedAt.trim()) body.burned_at = burnedAt.trim();

      const { data } = await axios.post(
        `${API}/api/admin/burns/disclose`,
        body,
        { headers: authHeaders() },
      );
      if (data?.announced) {
        toast.success("Burn disclosed + queued for X/Telegram approval.");
      } else if (data?.announce_error) {
        toast.warning(
          `Burn recorded — announce skipped: ${data.announce_error}`,
        );
      } else {
        toast.success("Burn disclosed.");
      }
      setAmount("");
      setTxSig("");
      setNote("");
      setBurnedAt("");
      await load();
    } catch (err: unknown) {
      // eslint-disable-next-line
      const errAny = err as any;
      const status = errAny?.response?.status;
      const detail = errAny?.response?.data?.detail;
      if (status === 409 && detail?.error === "duplicate_tx_signature") {
        toast.warning(
          "Already disclosed — this tx_signature is in the ledger.",
        );
        await load();
      } else {
        handleError(err, "Burn disclose failed");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const redact = async (burnId: string): Promise<void> => {
    if (
      !window.confirm(
        "Redact this burn? It will be hidden from the public counter (kept in audit log).",
      )
    ) {
      return;
    }
    try {
      await axios.post(
        `${API}/api/admin/burns/${burnId}/redact`,
        {},
        { headers: authHeaders() },
      );
      toast.success("Burn redacted.");
      await load();
    } catch (err) {
      handleError(err, "Burn redact failed");
    }
  };

  return (
    <Card data-testid="cabinet-incinerator-card">
      <CardHeader>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Flame size={16} className="text-[#FF6B35]" />
              Operation Incinerator
              <Badge variant="outline" data-testid="incinerator-status-badge">
                BURN LEDGER
              </Badge>
            </CardTitle>
            <CardDescription>
              Record on-chain $DEEPOTUS burns and (optionally) push a
              cynical Cabinet announcement through the Propaganda queue.
              Idempotent on tx_signature.
            </CardDescription>
          </div>
          {stats && (
            <div className="text-right text-xs font-mono space-y-0.5">
              <div className="text-foreground/55">
                Burned:{" "}
                <span className="text-[#FF6B35] font-medium">
                  {fmtBurnTokens(stats.total_burned)}
                </span>{" "}
                ({stats.burned_percent.toFixed(2)}%)
              </div>
              <div className="text-foreground/55">
                Real circulating:{" "}
                <span className="text-[#33FF33] font-medium">
                  {fmtBurnTokens(stats.effective_circulating)}
                </span>
              </div>
              <div className="text-[10px] text-foreground/40">
                excl. {stats.locked_percent.toFixed(0)}% locks (Treasury + Team)
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Disclose form */}
        <div className="rounded-md border border-border bg-muted/20 p-4 space-y-3">
          <div className="text-xs uppercase tracking-wider text-muted-foreground font-mono">
            Disclose a new burn
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <Label htmlFor="burn-amount" className="text-xs">
                Amount ($DEEPOTUS)
              </Label>
              <Input
                id="burn-amount"
                type="number"
                min="1"
                step="1"
                placeholder="e.g. 50000000"
                value={amount}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void =>
                  setAmount(e.target.value)
                }
                data-testid="incinerator-amount-input"
              />
            </div>
            <div>
              <Label htmlFor="burn-sig" className="text-xs">
                Tx signature (Solana)
              </Label>
              <Input
                id="burn-sig"
                placeholder="base58 signature"
                value={txSig}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void =>
                  setTxSig(e.target.value)
                }
                className="font-mono text-xs"
                data-testid="incinerator-sig-input"
              />
            </div>
            <div>
              <Label htmlFor="burn-when" className="text-xs">
                Burned at (ISO, optional)
              </Label>
              <Input
                id="burn-when"
                placeholder="2026-05-11T14:00:00Z (default: now)"
                value={burnedAt}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void =>
                  setBurnedAt(e.target.value)
                }
                className="font-mono text-xs"
                data-testid="incinerator-when-input"
              />
            </div>
            <div>
              <Label htmlFor="burn-lang" className="text-xs">
                Announcement language
              </Label>
              <select
                id="burn-lang"
                value={language}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>): void =>
                  setLanguage(e.target.value === "fr" ? "fr" : "en")
                }
                className="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
                data-testid="incinerator-lang-select"
              >
                <option value="en">EN</option>
                <option value="fr">FR</option>
              </select>
            </div>
          </div>
          <div>
            <Label htmlFor="burn-note" className="text-xs">
              Note (optional)
            </Label>
            <Textarea
              id="burn-note"
              placeholder="e.g. Q1 buyback · 60% of creator fees"
              value={note}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>): void =>
                setNote(e.target.value)
              }
              rows={2}
              maxLength={200}
              data-testid="incinerator-note-input"
            />
          </div>
          <div className="flex items-center justify-between gap-3 flex-wrap pt-1">
            <div className="flex items-center gap-2">
              <Switch
                id="burn-announce"
                checked={announce}
                onCheckedChange={(v: boolean): void => setAnnounce(v)}
                data-testid="incinerator-announce-toggle"
              />
              <Label htmlFor="burn-announce" className="text-xs cursor-pointer">
                Push to Propaganda queue (X + Telegram)
              </Label>
            </div>
            <Button
              onClick={(): void => {
                void submit();
              }}
              disabled={submitting}
              data-testid="incinerator-submit-btn"
            >
              {submitting ? (
                <>
                  <Loader2 size={14} className="mr-1.5 animate-spin" /> Disclosing…
                </>
              ) : (
                <>
                  <Flame size={14} className="mr-1.5" /> Disclose burn
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Ledger */}
        <div className="rounded-md border border-border bg-muted/30 p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <CheckCircle2 size={12} /> Burn ledger
              {loading && (
                <Loader2 size={12} className="animate-spin text-muted-foreground" />
              )}
            </div>
            <span className="text-[10px] font-mono text-muted-foreground">
              {burns.length} record{burns.length === 1 ? "" : "s"}
            </span>
          </div>
          {burns.length === 0 ? (
            <div className="text-xs text-muted-foreground py-3 text-center">
              No burns disclosed yet.
            </div>
          ) : (
            <ul
              className="space-y-2 max-h-80 overflow-auto pr-2"
              data-testid="incinerator-ledger-list"
            >
              {burns.map((b) => {
                const isRedacted = b.redacted_at !== null;
                return (
                  <li
                    key={b.id}
                    className={`rounded border border-border bg-background px-3 py-2 ${
                      isRedacted ? "opacity-50" : ""
                    }`}
                    data-testid={`incinerator-burn-${b.id}`}
                  >
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2 font-mono text-sm">
                        <Flame size={12} className="text-[#FF6B35]" />
                        <span className="font-medium">
                          {fmtBurnTokens(b.amount)}
                        </span>
                        {isRedacted && (
                          <Badge variant="destructive" className="text-[9px]">
                            REDACTED
                          </Badge>
                        )}
                        {b.queue_item_id && (
                          <Badge variant="secondary" className="text-[9px]">
                            ANNOUNCED
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <a
                          href={b.tx_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] font-mono text-[#22D3EE] hover:text-[#33FF33] inline-flex items-center gap-1"
                          data-testid={`incinerator-burn-tx-${b.id}`}
                        >
                          tx <ExternalLink size={10} />
                        </a>
                        {!isRedacted && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={(): void => {
                              void redact(b.id);
                            }}
                            data-testid={`incinerator-redact-${b.id}`}
                          >
                            <Trash2 size={12} />
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="mt-1 text-[10px] text-muted-foreground font-mono break-all">
                      {b.tx_signature.slice(0, 14)}…{b.tx_signature.slice(-8)}
                      <span className="ml-2">
                        · {new Date(b.burned_at).toLocaleString()}
                      </span>
                      {b.note && <span className="ml-2 italic">· {b.note}</span>}
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

// ---------------------------------------------------------------------
// Public tab entry-point
// ---------------------------------------------------------------------
export default function CabinetTab(): React.ReactElement {
  return (
    <div className="space-y-6" data-testid="propaganda-cabinet-tab">
      <WelcomeSignalCard />
      <InteractionBotCard />
      <IncineratorCard />
      <GiveawayExtractionCard />
    </div>
  );
}
