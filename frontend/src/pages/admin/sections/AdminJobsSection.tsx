/**
 * AdminJobsSection — "Jobs" tab inside AdminBots.
 *
 * Sprint 21 — extracted from the AdminBots monolith. Owns its own
 * `jobs` state + a 10-second auto-refresh poll. The parent page no
 * longer needs to know how the job list is rendered or refreshed.
 *
 * Self-contained: only requires `api` + `headers` from the parent.
 */

import { useCallback, useEffect, useState } from "react";
import axios from "axios";
// Sprint 22 — relaxed `AxiosRequestHeaders` to plain Record so the
// parent's `useMemo(() => ({ Authorization: ... }))` is assignable
// without an unsafe cast.
import { Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { logger } from "@/lib/logger";

const REFRESH_MS = 10_000;

interface JobInfo {
  id: string;
  trigger: string;
  next_run_time: string | null;
  max_instances: number;
  coalesce: boolean;
}

interface Props {
  api: string;
  headers: Record<string, string>;
}

export default function AdminJobsSection({ api, headers }: Props) {
  const [jobs, setJobs] = useState<JobInfo[]>([]);

  const load = useCallback(async () => {
    try {
      const { data } = await axios.get(`${api}/api/admin/bots/jobs`, {
        headers,
      });
      setJobs(Array.isArray(data) ? data : []);
    } catch (err) {
      logger.error(err);
    }
  }, [api, headers]);

  useEffect(() => {
    load();
    const id = window.setInterval(load, REFRESH_MS);
    return () => window.clearInterval(id);
  }, [load]);

  return (
    <div
      className="rounded-xl border border-border bg-card p-5"
      data-testid="jobs-section"
    >
      <div className="flex items-center gap-2 mb-4">
        <Clock size={16} className="text-muted-foreground" />
        <div className="font-display font-semibold">Live scheduler jobs</div>
        <Badge
          variant="outline"
          className="ml-auto font-mono text-[10px] uppercase tracking-widest"
        >
          {jobs.length} job{jobs.length > 1 ? "s" : ""}
        </Badge>
      </div>
      {jobs.length === 0 ? (
        <div className="py-8 text-center text-sm text-muted-foreground">
          No jobs registered.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-mono">
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-widest text-muted-foreground border-b border-border">
                <th className="py-2 pr-4">ID</th>
                <th className="py-2 pr-4">Trigger</th>
                <th className="py-2 pr-4">Next run</th>
                <th className="py-2 pr-4">Max inst</th>
                <th className="py-2">Coalesce</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr
                  key={j.id}
                  className="border-b border-border/50 hover:bg-background/40"
                  data-testid={`jobs-row-${j.id}`}
                >
                  <td className="py-2 pr-4 text-foreground">{j.id}</td>
                  <td className="py-2 pr-4 text-foreground/70">{j.trigger}</td>
                  <td className="py-2 pr-4 text-foreground/70">
                    {j.next_run_time
                      ? new Date(j.next_run_time).toLocaleString()
                      : "—"}
                  </td>
                  <td className="py-2 pr-4 text-foreground/70">{j.max_instances}</td>
                  <td className="py-2 text-foreground/70">
                    {j.coalesce ? "yes" : "no"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
