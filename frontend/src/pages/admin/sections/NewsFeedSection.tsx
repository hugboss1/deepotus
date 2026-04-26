import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Rss,
  RefreshCw,
  Newspaper,
  ExternalLink,
} from "lucide-react";
import { logger } from "@/lib/logger";

// eslint-disable-next-line
type AnyObj = Record<string, any>;

interface NewsItem {
  id: string;
  title: string;
  url: string;
  source: string | null;
}

interface NewsFeedConfig {
  enabled_for?: { x?: boolean; telegram?: boolean };
  fetch_interval_hours?: number;
  headlines_per_post?: number;
  feeds?: string[];
  default_feeds?: string[];
  keywords?: string[];
  default_keywords?: string[];
  last_refresh_at?: string | null;
  last_refresh_stats?: {
    fetched?: number;
    kept?: number;
    added?: number;
    feeds?: number;
  };
}

interface NewsFeedSectionProps {
  api: string;
  headers: { Authorization: string };
  config: AnyObj | null;
  setConfig: (cfg: AnyObj) => void;
  patchConfig: (patch: AnyObj, successMsg?: string) => Promise<void>;
}

export const NewsFeedSection: React.FC<NewsFeedSectionProps> = ({
  api,
  headers,
  config,
  setConfig,
  patchConfig,
}) => {
  const [news, setNews] = useState<{ items: NewsItem[] } | null>(null);
  const [newsBusy, setNewsBusy] = useState<boolean>(false);
  const [newsFeedsDraft, setNewsFeedsDraft] = useState<string>("");
  const [newsKeywordsDraft, setNewsKeywordsDraft] = useState<string>("");

  const newsFeedConfig: NewsFeedConfig = (config?.news_feed || {}) as NewsFeedConfig;

  const loadNews = async () => {
    try {
      const { data } = await axios.get(`${api}/api/admin/bots/news`, { headers });
      setNews(data);
    } catch (err) {
      logger.error(err);
    }
  };

  const refreshNewsNow = async () => {
    setNewsBusy(true);
    try {
      const { data } = await axios.post(
        `${api}/api/admin/bots/news/refresh`,
        {},
        { headers },
      );
      toast.success(
        `News refreshed — ${data.added} new / ${data.kept} kept / ${data.fetched} fetched`,
      );
      await loadNews();
    } catch (err: unknown) {
      logger.error(err);
      // eslint-disable-next-line
      toast.error((err as any)?.response?.data?.detail || "News refresh failed");
    } finally {
      setNewsBusy(false);
    }
  };

  useEffect(() => {
    loadNews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync drafts with config
  const feedsKey = JSON.stringify(newsFeedConfig.feeds || []);
  const keywordsKey = JSON.stringify(newsFeedConfig.keywords || []);
  useEffect(() => {
    const nf = newsFeedConfig;
    if (!nf || Object.keys(nf).length === 0) return;
    const feedsList =
      nf.feeds && nf.feeds.length > 0 ? nf.feeds : nf.default_feeds || [];
    const kwList =
      nf.keywords && nf.keywords.length > 0
        ? nf.keywords
        : nf.default_keywords || [];
    setNewsFeedsDraft(feedsList.join("\n"));
    setNewsKeywordsDraft(kwList.join(", "));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feedsKey, keywordsKey]);

  return (
    <div
      className="rounded-xl border border-border bg-card p-5 space-y-4"
      data-testid="news-feed-section"
    >
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Rss size={16} className="text-[#F59E0B]" />
          <div className="font-display font-semibold">
            News feed · geopolitics + macro
          </div>
          <Badge
            variant="outline"
            className="font-mono text-[10px] uppercase tracking-widest"
          >
            inspiration source
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-muted-foreground">
            last refresh:{" "}
            {newsFeedConfig.last_refresh_at
              ? new Date(newsFeedConfig.last_refresh_at).toLocaleString()
              : "—"}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={refreshNewsNow}
            disabled={newsBusy}
            className="rounded-[var(--btn-radius)]"
            data-testid="news-feed-refresh-btn"
          >
            <RefreshCw
              size={13}
              className={`mr-1 ${newsBusy ? "animate-spin" : ""}`}
            />
            Refresh now
          </Button>
        </div>
      </div>

      {newsFeedConfig.last_refresh_stats && (
        <div className="font-mono text-[11px] text-muted-foreground">
          fetched{" "}
          <span className="text-foreground/80">
            {newsFeedConfig.last_refresh_stats.fetched ?? "?"}
          </span>
          {" · "}kept{" "}
          <span className="text-foreground/80">
            {newsFeedConfig.last_refresh_stats.kept ?? "?"}
          </span>
          {" · "}new{" "}
          <span className="text-[#F59E0B]">
            {newsFeedConfig.last_refresh_stats.added ?? "?"}
          </span>
          {" · "}feeds{" "}
          <span className="text-foreground/80">
            {newsFeedConfig.last_refresh_stats.feeds ?? "?"}
          </span>
        </div>
      )}

      {/* Per-platform toggles */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {(["x", "telegram"] as const).map((plat) => (
          <div
            key={plat}
            className="flex items-center justify-between rounded-lg border border-border bg-background/40 p-3"
          >
            <div>
              <div className="font-display font-semibold capitalize">
                {plat}
              </div>
              <div className="text-xs text-muted-foreground">
                Inject latest headlines as Prophet inspiration
              </div>
            </div>
            <Switch
              checked={Boolean(newsFeedConfig.enabled_for?.[plat])}
              onCheckedChange={(checked: boolean) =>
                patchConfig(
                  {
                    news_feed: {
                      enabled_for: {
                        ...(newsFeedConfig.enabled_for || {}),
                        [plat]: checked,
                      },
                    },
                  },
                  `News feed for ${plat} ${checked ? "enabled" : "disabled"}`,
                )
              }
              data-testid={`news-feed-toggle-${plat}`}
            />
          </div>
        ))}
      </div>

      {/* Interval + headlines per post */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            Refresh interval (h)
          </Label>
          <Input
            type="number"
            min="1"
            max="24"
            value={newsFeedConfig.fetch_interval_hours ?? 6}
            onChange={(e) =>
              setConfig({
                ...config,
                news_feed: {
                  ...newsFeedConfig,
                  fetch_interval_hours: Number(e.target.value),
                },
              })
            }
            onBlur={(e) =>
              patchConfig(
                {
                  news_feed: {
                    fetch_interval_hours: Number(e.target.value),
                  },
                },
                "News refresh interval saved",
              )
            }
            className="mt-2 font-mono"
            data-testid="news-feed-interval"
          />
        </div>
        <div>
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            Headlines per post
          </Label>
          <Input
            type="number"
            min="0"
            max="10"
            value={newsFeedConfig.headlines_per_post ?? 5}
            onChange={(e) =>
              setConfig({
                ...config,
                news_feed: {
                  ...newsFeedConfig,
                  headlines_per_post: Number(e.target.value),
                },
              })
            }
            onBlur={(e) =>
              patchConfig(
                {
                  news_feed: {
                    headlines_per_post: Number(e.target.value),
                  },
                },
                "Headlines per post saved",
              )
            }
            className="mt-2 font-mono"
            data-testid="news-feed-headlines"
          />
        </div>
      </div>

      {/* RSS feeds editor */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            RSS feeds (one per line)
          </Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
            onClick={() => {
              const defaults = newsFeedConfig.default_feeds || [];
              setNewsFeedsDraft(defaults.join("\n"));
              patchConfig(
                { news_feed: { feeds: [] } },
                "Reset to default feeds",
              );
            }}
            data-testid="news-feed-feeds-reset"
          >
            Reset to default
          </Button>
        </div>
        <textarea
          value={newsFeedsDraft}
          onChange={(e) => setNewsFeedsDraft(e.target.value)}
          onBlur={() =>
            patchConfig(
              {
                news_feed: {
                  feeds: newsFeedsDraft
                    .split(/\r?\n/)
                    .map((s) => s.trim())
                    .filter(Boolean),
                },
              },
              "RSS feeds saved",
            )
          }
          rows={6}
          className="w-full mt-1 rounded-md border border-border bg-background px-3 py-2 font-mono text-[11px] text-foreground/85 leading-relaxed focus:outline-none focus:ring-2 focus:ring-[#F59E0B]/40"
          spellCheck={false}
          placeholder="https://feeds.bbci.co.uk/news/world/rss.xml"
          data-testid="news-feed-urls"
        />
      </div>

      {/* Keywords editor */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            Filter keywords (comma separated)
          </Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
            onClick={() => {
              const defaults = newsFeedConfig.default_keywords || [];
              setNewsKeywordsDraft(defaults.join(", "));
              patchConfig(
                { news_feed: { keywords: [] } },
                "Reset to default keywords",
              );
            }}
            data-testid="news-feed-keywords-reset"
          >
            Reset to default
          </Button>
        </div>
        <textarea
          value={newsKeywordsDraft}
          onChange={(e) => setNewsKeywordsDraft(e.target.value)}
          onBlur={() =>
            patchConfig(
              {
                news_feed: {
                  keywords: newsKeywordsDraft
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                },
              },
              "Keywords saved",
            )
          }
          rows={3}
          className="w-full mt-1 rounded-md border border-border bg-background px-3 py-2 font-mono text-[11px] text-foreground/85 leading-relaxed focus:outline-none focus:ring-2 focus:ring-[#F59E0B]/40"
          spellCheck={false}
          placeholder="war, ukraine, fed, ECB, inflation, ..."
          data-testid="news-feed-keywords"
        />
      </div>

      {/* Headlines preview */}
      <div className="rounded-lg border border-border bg-background/40 p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Newspaper size={13} className="text-[#2DD4BF]" />
            <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Latest kept headlines (top 5)
            </div>
          </div>
          <span className="font-mono text-[10px] text-muted-foreground">
            {news?.items?.length ?? 0} item(s) buffered
          </span>
        </div>
        {news?.items && news.items.length > 0 ? (
          <ul
            className="space-y-1.5 text-xs leading-relaxed"
            data-testid="news-feed-preview-list"
          >
            {news.items.slice(0, 5).map((it) => (
              <li
                key={it.id}
                className="flex items-start gap-2"
                data-testid={`news-feed-item-${it.id}`}
              >
                <span className="font-mono text-[10px] uppercase tracking-widest text-[#F59E0B] flex-none">
                  {(it.source || "?").slice(0, 18)}
                </span>
                <a
                  href={it.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground/85 hover:underline inline-flex items-baseline gap-1 min-w-0"
                >
                  <span className="truncate">{it.title}</span>
                  <ExternalLink
                    size={10}
                    className="flex-none text-muted-foreground"
                  />
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-xs text-muted-foreground italic">
            No items yet — click "Refresh now" to fetch the feeds.
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsFeedSection;
