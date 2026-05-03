/**
 * NewsRepostSection — Bots Control admin panel for the news repost engine.
 *
 * Self-contained: owns its own state + API calls. Parent only renders
 * `<NewsRepostSection api={API} headers={headers} />`. Extracted from the
 * 2700-line AdminBots.jsx (Sprint 5 split phase).
 *
 * Auto-relays the top kept RSS headlines verbatim (no LLM) to X & Telegram,
 * with dedup, daily cap, "wait after Prophet" guard, and dry-run mode when
 * platform credentials aren't yet provisioned (Phases 3/4/5).
 *
 * Behaviour parity with the old inline section is preserved 1:1; the
 * data-testids are unchanged.
 */
import { useCallback, useEffect, useState } from "react";
import axios from "axios";
// Sprint 22 — `AxiosRequestHeaders` was too strict for our useMemo header object.
import { RefreshCw, Newspaper } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import type {
  NewsRepostStatus,
  NewsRepostTestResult,
  NewsRepostQueueItem,
} from "@/types";

interface RepostPatchBody {
  enabled_for?: { x?: boolean; telegram?: boolean };
  interval_minutes?: number;
  delay_after_refresh_minutes?: number;
  wait_after_prophet_post_minutes?: number;
  daily_cap?: number;
  prefix_fr?: string;
  prefix_en?: string;
}

interface Props {
  api: string;
  headers: Record<string, string>;
}

type Platform = "telegram" | "x";

export default function NewsRepostSection({ api, headers }: Props) {
  const [repost, setRepost] = useState<NewsRepostStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [testBusy, setTestBusy] = useState(false);
  const [testResult, setTestResult] = useState<NewsRepostTestResult | null>(
    null,
  );

  const load = useCallback(async () => {
    try {
      const { data } = await axios.get<NewsRepostStatus>(
        `${api}/api/admin/bots/news-repost/status`,
        { headers },
      );
      setRepost(data);
    } catch (err) {
      logger.error(err);
    }
  }, [api, headers]);

  useEffect(() => {
    load();
  }, [load]);

  async function patch(body: RepostPatchBody) {
    setBusy(true);
    try {
      await axios.put(
        `${api}/api/admin/bots/config`,
        { news_repost: body },
        { headers },
      );
      await load();
      toast.success("News repost config updated");
    } catch (err) {
      logger.error(err);
      toast.error("Could not update repost config");
    } finally {
      setBusy(false);
    }
  }

  async function sendTest(platform: Platform) {
    setTestBusy(true);
    setTestResult(null);
    try {
      const { data } = await axios.post<NewsRepostTestResult>(
        `${api}/api/admin/bots/news-repost/test-send`,
        { platform, lang: "fr" },
        { headers },
      );
      setTestResult(data);
      const status = data?.status || "unknown";
      if (status === "sent") toast.success(`Reposted on ${platform}`);
      else if (status === "dry_run")
        toast.success(`Dry-run on ${platform} (no creds)`);
      else toast.error(`Status: ${status}`);
      await load();
    } catch (err) {
      logger.error(err);
      toast.error("Test repost failed");
    } finally {
      setTestBusy(false);
    }
  }

  // ---- Helpers for inline state mutation while the user types ----
  const updateConfig = (patchFn: (cfg: NewsRepostStatus["config"]) => NewsRepostStatus["config"]) => {
    setRepost((prev) => (prev ? { ...prev, config: patchFn(prev.config) } : prev));
  };

  const liveCreds =
    !!repost?.credentials_present?.x || !!repost?.credentials_present?.telegram;

  return (
    <div
      className="rounded-xl border border-border bg-card p-5 space-y-4"
      data-testid="news-repost-section"
    >
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Newspaper size={16} className="text-[#F59E0B]" />
          <div className="font-display font-semibold">
            News repost · auto-relay X &amp; Telegram
          </div>
          <Badge
            variant="outline"
            className="font-mono text-[10px] uppercase tracking-widest"
            data-testid="news-repost-mode-badge"
          >
            {liveCreds ? "live · partial" : "dry-run · no creds yet"}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={load}
          disabled={busy}
          data-testid="news-repost-refresh-btn"
        >
          <RefreshCw size={14} className="mr-1.5" /> Refresh
        </Button>
      </div>

      <p className="text-xs text-muted-foreground leading-relaxed">
        Reposts the top kept RSS headlines verbatim (no LLM) on X and
        Telegram, prefixed with{" "}
        <code className="font-mono text-[10px] bg-secondary/40 px-1.5 py-0.5 rounded">
          {repost?.config?.prefix_fr || "⚡ INTERCEPTÉ ·"}
        </code>
        . Runs in parallel with the Prophet posts and waits{" "}
        <strong>
          {repost?.config?.wait_after_prophet_post_minutes || 2} min
        </strong>{" "}
        after a Prophet post to avoid collisions. Dedup is enforced per-link,
        per-platform.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {(["telegram", "x"] as const).map((p) => (
          <PlatformCard
            key={p}
            platform={p}
            repost={repost}
            busy={busy}
            testBusy={testBusy}
            onToggle={(v) => patch({ enabled_for: { [p]: v } })}
            onTest={() => sendTest(p)}
          />
        ))}
      </div>

      <NumericControls
        repost={repost}
        onPatch={patch}
        onLiveUpdate={updateConfig}
      />

      <PrefixControls repost={repost} onPatch={patch} onLiveUpdate={updateConfig} />

      <QueuePreview repost={repost} />

      <TestResult testResult={testResult} />
    </div>
  );
}

// ---------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------
interface PlatformCardProps {
  platform: Platform;
  repost: NewsRepostStatus | null;
  busy: boolean;
  testBusy: boolean;
  onToggle: (v: boolean) => void;
  onTest: () => void;
}

function PlatformCard({
  platform,
  repost,
  busy,
  testBusy,
  onToggle,
  onTest,
}: PlatformCardProps) {
  return (
    <div
      className="rounded-lg border border-border bg-secondary/30 p-3 flex items-center justify-between gap-2"
      data-testid={`news-repost-platform-${platform}`}
    >
      <div>
        <div className="text-xs font-medium uppercase tracking-widest">
          {platform}
        </div>
        <div className="text-[10px] text-muted-foreground font-mono">
          sent today: {repost?.today_per_platform?.[platform] ?? 0} /{" "}
          {repost?.config?.daily_cap ?? 10}
          {!repost?.credentials_present?.[platform] && (
            <span className="ml-2 text-[#F59E0B]">· dry-run only</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Switch
          checked={!!repost?.config?.enabled_for?.[platform]}
          disabled={busy}
          onCheckedChange={onToggle}
          data-testid={`news-repost-toggle-${platform}`}
        />
        <Button
          size="sm"
          variant="outline"
          onClick={onTest}
          disabled={testBusy}
          className="font-mono uppercase tracking-widest text-[10px]"
          data-testid={`news-repost-test-${platform}`}
        >
          Test
        </Button>
      </div>
    </div>
  );
}

interface NumericControlsProps {
  repost: NewsRepostStatus | null;
  onPatch: (body: RepostPatchBody) => void;
  onLiveUpdate: (
    patchFn: (cfg: NewsRepostStatus["config"]) => NewsRepostStatus["config"],
  ) => void;
}

function NumericControls({ repost, onPatch, onLiveUpdate }: NumericControlsProps) {
  const items: Array<{
    label: string;
    field:
      | "interval_minutes"
      | "daily_cap"
      | "wait_after_prophet_post_minutes"
      | "delay_after_refresh_minutes";
    fallback: number;
    min: number;
    max: number;
    testId: string;
  }> = [
    {
      label: "Interval (min)",
      field: "interval_minutes",
      fallback: 30,
      min: 5,
      max: 720,
      testId: "news-repost-interval-input",
    },
    {
      label: "Daily cap",
      field: "daily_cap",
      fallback: 10,
      min: 0,
      max: 200,
      testId: "news-repost-cap-input",
    },
    {
      label: "Wait after Prophet (min)",
      field: "wait_after_prophet_post_minutes",
      fallback: 2,
      min: 0,
      max: 120,
      testId: "news-repost-wait-input",
    },
    {
      label: "Delay after RSS refresh (min)",
      field: "delay_after_refresh_minutes",
      fallback: 5,
      min: 0,
      max: 120,
      testId: "news-repost-delay-input",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {items.map(({ label, field, fallback, min, max, testId }) => (
        <div
          key={field}
          className="rounded-lg border border-border bg-secondary/30 p-3"
        >
          <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest mb-1">
            {label}
          </div>
          <Input
            type="number"
            min={min}
            max={max}
            value={repost?.config?.[field] ?? fallback}
            onChange={(e) =>
              onLiveUpdate((cfg) => ({
                ...cfg,
                [field]: Number(e.target.value || fallback),
              }))
            }
            onBlur={(e) =>
              onPatch({
                [field]: Math.max(
                  min,
                  Math.min(max, Number(e.target.value || fallback)),
                ),
              })
            }
            data-testid={testId}
            className="font-mono text-sm"
          />
        </div>
      ))}
    </div>
  );
}

interface PrefixControlsProps {
  repost: NewsRepostStatus | null;
  onPatch: (body: RepostPatchBody) => void;
  onLiveUpdate: (
    patchFn: (cfg: NewsRepostStatus["config"]) => NewsRepostStatus["config"],
  ) => void;
}

function PrefixControls({ repost, onPatch, onLiveUpdate }: PrefixControlsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {(["fr", "en"] as const).map((lng) => {
        const field = `prefix_${lng}` as "prefix_fr" | "prefix_en";
        return (
          <div
            key={lng}
            className="rounded-lg border border-border bg-secondary/30 p-3"
          >
            <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest mb-1">
              Prefix · {lng.toUpperCase()}
            </div>
            <Input
              type="text"
              maxLength={80}
              value={repost?.config?.[field] ?? ""}
              onChange={(e) =>
                onLiveUpdate((cfg) => ({ ...cfg, [field]: e.target.value }))
              }
              onBlur={(e) => onPatch({ [field]: e.target.value })}
              data-testid={`news-repost-prefix-${lng}`}
              className="font-mono text-sm"
            />
          </div>
        );
      })}
    </div>
  );
}

function QueuePreview({ repost }: { repost: NewsRepostStatus | null }) {
  return (
    <div
      className="rounded-lg border border-border bg-[#0B0D10]/85 text-white p-3"
      data-testid="news-repost-queue"
    >
      <div className="font-mono text-[10px] uppercase tracking-widest text-white/60 mb-2">
        Queue · next 3 per platform (what would go out)
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {(["telegram", "x"] as const).map((p) => (
          <PlatformQueue
            key={p}
            platform={p}
            items={repost?.queue_preview?.[p] || []}
          />
        ))}
      </div>
    </div>
  );
}

function PlatformQueue({
  platform,
  items,
}: {
  platform: Platform;
  items: NewsRepostQueueItem[];
}) {
  return (
    <div className="space-y-2" data-testid={`news-repost-queue-${platform}`}>
      <div className="font-mono text-[10px] uppercase tracking-widest text-[#F59E0B]">
        {platform}
      </div>
      {items.length === 0 && (
        <div className="font-mono text-[10px] text-white/45 italic">
          — empty queue —
        </div>
      )}
      {items.map((it, i) => (
        <div
          key={`${platform}-${it.url || i}`}
          className="rounded-md border border-white/10 px-2 py-1.5"
        >
          <div className="text-[10px] text-white/55 font-mono uppercase tracking-widest">
            {it.source || "—"}
          </div>
          <div className="text-xs text-white/90">{it.title}</div>
          <details className="mt-1">
            <summary className="cursor-pointer text-[10px] uppercase tracking-widest text-white/50">
              Preview text
            </summary>
            <pre className="mt-1 font-mono text-[10.5px] text-white/85 whitespace-pre-wrap break-words leading-relaxed">
              {it.preview_text}
            </pre>
          </details>
        </div>
      ))}
    </div>
  );
}

function TestResult({
  testResult,
}: {
  testResult: NewsRepostTestResult | null;
}) {
  if (!testResult) return null;
  return (
    <div
      className="rounded-md border border-border bg-card p-2.5 font-mono text-[11px] space-y-1"
      data-testid="news-repost-test-result"
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="uppercase tracking-widest text-muted-foreground">
          last test
        </span>
        <Badge
          variant={testResult.status === "sent" ? "default" : "outline"}
          className="text-[10px] uppercase"
        >
          {testResult.platform} · {testResult.status}
        </Badge>
      </div>
      {testResult.title && (
        <div className="text-foreground/85">{testResult.title}</div>
      )}
      {testResult.preview_text && (
        <pre className="bg-secondary/40 p-2 rounded text-[10.5px] whitespace-pre-wrap break-words">
          {testResult.preview_text}
        </pre>
      )}
      {testResult.error && (
        <div className="text-destructive">{testResult.error}</div>
      )}
      {testResult.hint && (
        <div className="text-muted-foreground italic">{testResult.hint}</div>
      )}
    </div>
  );
}
