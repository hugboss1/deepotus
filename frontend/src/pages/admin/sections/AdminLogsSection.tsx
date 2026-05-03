/**
 * AdminLogsSection — "Logs" tab inside AdminBots.
 *
 * Sprint 21 — extracted from the AdminBots monolith. Owns the post-
 * attempts table, the platform / status filters, the histogram of
 * status counts and a 10 s auto-refresh poll. Parent page no longer
 * needs to know how logs are paginated or filtered.
 */

import { useCallback, useEffect, useState } from "react";
import axios from "axios";
// Sprint 22 — relaxed `AxiosRequestHeaders` to plain Record so the
// parent's `useMemo(() => ({ Authorization: ... }))` is assignable
// without an unsafe cast.
import { TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { logger } from "@/lib/logger";

const REFRESH_MS = 10_000;

const STATUS_COLOR: Record<string, string> = {
  heartbeat: "#18C964",
  posted: "#2DD4BF",
  killed: "#E11D48",
  skipped: "#F59E0B",
  failed: "#E11D48",
};

interface PostItem {
  id: string;
  created_at: string | null;
  platform: string;
  content_type: string;
  status: string;
  content: string | null;
  error: string | null;
}

interface PostsResponse {
  items: PostItem[];
  total: number;
  status_counts: Record<string, number>;
}

interface Props {
  api: string;
  headers: Record<string, string>;
}

export default function AdminLogsSection({ api, headers }: Props) {
  const [posts, setPosts] = useState<PostsResponse | null>(null);
  const [platformFilter, setPlatformFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: "30", skip: "0" });
      if (platformFilter !== "all") params.set("platform", platformFilter);
      if (statusFilter !== "all") params.set("status", statusFilter);
      const { data } = await axios.get<PostsResponse>(
        `${api}/api/admin/bots/posts?${params.toString()}`,
        { headers },
      );
      setPosts(data);
    } catch (err) {
      logger.error(err);
    }
  }, [api, headers, platformFilter, statusFilter]);

  useEffect(() => {
    load();
    const id = window.setInterval(load, REFRESH_MS);
    return () => window.clearInterval(id);
  }, [load]);

  const statusCounts = posts?.status_counts || {};
  const items = posts?.items || [];

  return (
    <div className="space-y-4" data-testid="logs-section">
      {/* Status histogram */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(statusCounts).map(([s, n]) => (
          <Badge
            key={s}
            variant="outline"
            className="font-mono text-[10px] uppercase tracking-widest"
            style={{
              borderColor: `${STATUS_COLOR[s] || "#888"}66`,
              color: STATUS_COLOR[s] || "#888",
            }}
            data-testid={`logs-count-${s}`}
          >
            <TrendingUp size={10} className="mr-1" /> {s} · {n}
          </Badge>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Label className="text-xs text-muted-foreground">Platform</Label>
          <Select value={platformFilter} onValueChange={setPlatformFilter}>
            <SelectTrigger
              className="w-36 h-8"
              data-testid="logs-platform-filter"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="x">X</SelectItem>
              <SelectItem value="telegram">Telegram</SelectItem>
              <SelectItem value="system">System</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Label className="text-xs text-muted-foreground">Status</Label>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger
              className="w-36 h-8"
              data-testid="logs-status-filter"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="heartbeat">Heartbeat</SelectItem>
              <SelectItem value="posted">Posted</SelectItem>
              <SelectItem value="killed">Killed</SelectItem>
              <SelectItem value="skipped">Skipped</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Post log table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-background/40">
              <tr className="text-left text-[10px] uppercase tracking-widest text-muted-foreground">
                <th className="py-2.5 px-4">When</th>
                <th className="py-2.5 px-4">Platform</th>
                <th className="py-2.5 px-4">Type</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Content / error</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="py-10 text-center text-muted-foreground font-mono text-xs"
                  >
                    No entries match the filters yet.
                  </td>
                </tr>
              ) : (
                items.map((p) => (
                  <tr
                    key={p.id}
                    className="border-t border-border/50 hover:bg-background/40"
                    data-testid={`logs-row-${p.id}`}
                  >
                    <td className="py-2 px-4 font-mono text-[11px] text-foreground/70 whitespace-nowrap">
                      {p.created_at
                        ? new Date(p.created_at).toLocaleTimeString()
                        : "—"}
                    </td>
                    <td className="py-2 px-4 font-mono text-xs text-foreground/80 uppercase tracking-widest">
                      {p.platform}
                    </td>
                    <td className="py-2 px-4 font-mono text-xs text-foreground/80">
                      {p.content_type}
                    </td>
                    <td className="py-2 px-4">
                      <span
                        className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full border"
                        style={{
                          borderColor: `${STATUS_COLOR[p.status] || "#888"}66`,
                          color: STATUS_COLOR[p.status] || "#888",
                        }}
                      >
                        {p.status}
                      </span>
                    </td>
                    <td className="py-2 px-4 text-xs text-foreground/75 max-w-sm truncate">
                      {p.error ? (
                        <span className="text-[#E11D48]">{p.error}</span>
                      ) : (
                        p.content || "—"
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      <div className="font-mono text-[10px] text-muted-foreground">
        showing {items.length} of {posts?.total ?? 0} · auto-refresh every 10 s
      </div>
    </div>
  );
}
