import React from "react";

interface StatCardProps {
  label: string;
  value: number | string;
  testid: string;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, testid }) => {
  return (
    <div data-testid={testid} className="rounded-xl border border-border bg-card p-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
        {label}
      </div>
      <div className="tabular font-display font-semibold text-2xl md:text-3xl mt-1">
        {value}
      </div>
    </div>
  );
};
