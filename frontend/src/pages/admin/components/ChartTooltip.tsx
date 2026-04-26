import React from "react";

// eslint-disable-next-line
interface TooltipPayloadItem {
  dataKey: string;
  name: string;
  // eslint-disable-next-line
  value: any;
  color: string;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}

export const ChartTooltip: React.FC<ChartTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-[var(--shadow-elev-1)] font-mono text-xs">
      <div className="text-foreground font-semibold">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tabular text-foreground/80">
          <span
            className="inline-block w-2 h-2 rounded-full mr-2 align-middle"
            style={{ background: p.color }}
          />
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
};
