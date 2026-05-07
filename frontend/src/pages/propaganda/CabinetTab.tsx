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
  Loader2,
  RadioTower,
  Send,
  Sparkles,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
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
// Public tab entry-point
// ---------------------------------------------------------------------
export default function CabinetTab(): React.ReactElement {
  return (
    <div className="space-y-6" data-testid="propaganda-cabinet-tab">
      <WelcomeSignalCard />
      <InteractionBotCard />
    </div>
  );
}
