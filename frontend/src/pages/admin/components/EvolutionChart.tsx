import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RTooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { ChartTooltip } from "./ChartTooltip";

function formatDateShort(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

interface EvolutionPoint {
  date: string;
  whitelist: number;
  chat: number;
}

interface EvolutionChartProps {
  evolution: EvolutionPoint[];
  days: number;
  onChangeDays: (days: number) => void;
}

export const EvolutionChart: React.FC<EvolutionChartProps> = ({ evolution, days, onChangeDays }) => {
  const chartData = React.useMemo(
    () =>
      evolution.map((p) => ({
        date: formatDateShort(p.date),
        rawDate: p.date,
        whitelist: p.whitelist,
        chat: p.chat,
      })),
    [evolution],
  );

  return (
    <div className="mt-8 rounded-xl border border-border bg-card p-4 md:p-5" data-testid="admin-evolution">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">Evolution</div>
          <div className="font-display font-semibold">Whitelist & Transmissions · cumulative</div>
        </div>
        <div className="inline-flex items-center gap-1 rounded-[var(--btn-radius)] border border-border bg-background p-0.5">
          {[7, 30, 90].map((d) => {
            const active = d === days;
            return (
              <button
                key={d}
                type="button"
                onClick={() => onChangeDays(d)}
                className={`px-3 py-1 rounded-[8px] font-mono text-[11px] uppercase tracking-widest transition-colors ${
                  active ? "bg-foreground text-background" : "text-foreground/70 hover:text-foreground"
                }`}
                data-testid={`admin-evolution-range-${d}`}
              >
                {d}d
              </button>
            );
          })}
        </div>
      </div>
      <div className="h-[260px] w-full" data-testid="admin-chart-whitelist">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
            <defs>
              <linearGradient id="gW" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2DD4BF" stopOpacity={0.6} />
                <stop offset="100%" stopColor="#2DD4BF" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="gC" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.55} />
                <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="date" tick={{ fontFamily: "IBM Plex Mono", fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={{ stroke: "hsl(var(--border))" }} />
            <YAxis tick={{ fontFamily: "IBM Plex Mono", fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={{ stroke: "hsl(var(--border))" }} allowDecimals={false} />
            <RTooltip content={<ChartTooltip />} />
            <Area type="monotone" dataKey="whitelist" name="Whitelist" stroke="#2DD4BF" strokeWidth={2} fill="url(#gW)" />
            <Area type="monotone" dataKey="chat" name="Chat messages" stroke="#F59E0B" strokeWidth={2} fill="url(#gC)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
