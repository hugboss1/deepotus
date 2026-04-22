import React, { useMemo } from "react";

const DAY_LABELS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const DAY_LABELS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

function rgb(intensity) {
  // intensity 0..1 → interpolate background
  // light theme: white → teal
  // dark theme: css handled via class; we inline color
  const t = Math.min(1, Math.max(0, intensity));
  // teal #2DD4BF  -> rgb(45, 212, 191)
  const r = Math.round(234 * (1 - t) + 45 * t);
  const g = Math.round(234 * (1 - t) + 212 * t);
  const b = Math.round(234 * (1 - t) + 191 * t);
  return `rgb(${r}, ${g}, ${b})`;
}

export default function ActivityHeatmap({ data, lang = "en" }) {
  // data: 7 x 24 matrix
  const labels = lang === "fr" ? DAY_LABELS_FR : DAY_LABELS_EN;
  const max = useMemo(() => {
    let m = 0;
    if (Array.isArray(data)) {
      for (const row of data) for (const v of row) if (v > m) m = v;
    }
    return m || 1;
  }, [data]);

  if (!Array.isArray(data) || data.length !== 7) {
    return (
      <div className="text-center text-muted-foreground font-mono text-xs py-10">
        {lang === "fr" ? "Données indisponibles" : "Data unavailable"}
      </div>
    );
  }

  return (
    <div data-testid="activity-heatmap" className="w-full">
      <div className="overflow-x-auto">
        <table className="w-full border-separate" style={{ borderSpacing: 2 }}>
          <thead>
            <tr>
              <th className="w-10"></th>
              {Array.from({ length: 24 }).map((_, h) => (
                <th
                  key={h}
                  className="font-mono text-[9px] text-muted-foreground text-center font-normal"
                >
                  {h % 3 === 0 ? String(h).padStart(2, "0") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, d) => (
              <tr key={d}>
                <td className="font-mono text-[10px] text-muted-foreground pr-2 text-right align-middle">
                  {labels[d]}
                </td>
                {row.map((v, h) => {
                  const intensity = max > 0 ? v / max : 0;
                  return (
                    <td
                      key={h}
                      title={`${labels[d]} ${String(h).padStart(2, "0")}h UTC · ${v} msg`}
                      data-testid={`heatmap-cell-${d}-${h}`}
                      className="h-5 rounded-[3px] transition-colors"
                      style={{
                        background: rgb(intensity),
                        border: intensity === 0 ? "1px solid hsl(var(--border))" : "none",
                      }}
                    />
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex items-center justify-between text-[10px] font-mono text-muted-foreground">
        <span>
          {lang === "fr"
            ? "Activité chat par heure (UTC) · 30 derniers jours"
            : "Chat activity per hour (UTC) · last 30 days"}
        </span>
        <div className="flex items-center gap-2">
          <span>{lang === "fr" ? "Moins" : "Less"}</span>
          {[0.15, 0.35, 0.6, 0.85, 1.0].map((i) => (
            <span
              key={i}
              className="inline-block w-3 h-3 rounded-[3px]"
              style={{ background: rgb(i) }}
            />
          ))}
          <span>{lang === "fr" ? "Plus" : "More"}</span>
        </div>
      </div>
    </div>
  );
}
