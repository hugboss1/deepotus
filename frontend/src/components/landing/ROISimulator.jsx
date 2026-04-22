import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Calculator } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n/I18nProvider";

const PRICE = 0.0005;

function fmtEur(n) {
  try {
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 2,
    }).format(n);
  } catch {
    return `€${n.toFixed(2)}`;
  }
}

function fmtInt(n) {
  try {
    return new Intl.NumberFormat("fr-FR").format(Math.floor(n));
  } catch {
    return Math.floor(n).toLocaleString();
  }
}

export default function ROISimulator() {
  const { t } = useI18n();
  const [amount, setAmount] = useState(500);

  const tokens = useMemo(() => {
    const a = Number(amount);
    if (!isFinite(a) || a <= 0) return 0;
    return a / PRICE;
  }, [amount]);

  const scenarios = t("roi.scenarios") || {};

  const card = (key) => {
    const s = scenarios[key];
    if (!s) return null;
    const a = Number(amount) || 0;
    const val = a * s.multiplier;
    return (
      <div className="rounded-xl border border-border bg-card p-5 h-full flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <Badge variant="outline" className="font-mono uppercase tracking-widest text-[10px]">
            {key}
          </Badge>
          <span className="tabular font-mono text-sm text-foreground/70">
            x{s.multiplier}
          </span>
        </div>
        <div className="font-display font-semibold">{s.label}</div>
        <div className="text-sm text-foreground/70 leading-snug">{s.caption}</div>
        <div className="mt-auto">
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {t("roi.resultLabel")}
          </div>
          <div className="tabular font-mono text-2xl font-semibold">
            {fmtEur(val)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <section
      id="roi"
      className="py-14 sm:py-18 lg:py-24 border-t border-border bg-secondary/30"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("roi.kicker")}
        </div>
        <div className="flex items-center gap-3 mt-2">
          <Calculator size={22} className="text-accent" />
          <h2 className="font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
            {t("roi.title")}
          </h2>
        </div>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Input */}
          <div className="lg:col-span-5">
            <div className="rounded-xl border border-border bg-card p-5">
              <label
                htmlFor="roi-amount"
                className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground"
              >
                {t("roi.inputLabel")}
              </label>
              <div className="mt-2 flex items-center gap-2">
                <span className="tabular font-mono text-xl text-foreground/70">
                  €
                </span>
                <Input
                  id="roi-amount"
                  data-testid="roi-amount-input"
                  type="number"
                  min={0}
                  step="10"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder={t("roi.placeholder")}
                  className="tabular font-mono text-2xl h-14"
                />
              </div>

              <div className="mt-5 rounded-lg border border-border bg-background p-4">
                <div className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                  {t("roi.tokenLabel")}
                </div>
                <div
                  className="tabular font-mono text-3xl font-semibold"
                  data-testid="roi-tokens-output"
                >
                  {fmtInt(tokens)}
                </div>
                <div className="tabular font-mono text-xs text-muted-foreground mt-1">
                  @ €0.0005 / token
                </div>
              </div>
            </div>
          </div>

          {/* Scenarios */}
          <div className="lg:col-span-7">
            <div className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground mb-2">
              {t("roi.scenariosTitle")}
            </div>
            <Tabs defaultValue="base" className="w-full">
              <TabsList className="grid grid-cols-3 w-full md:w-[420px]">
                <TabsTrigger value="brutal" data-testid="roi-tab-brutal">
                  Brutal
                </TabsTrigger>
                <TabsTrigger value="base" data-testid="roi-tab-base">
                  Base
                </TabsTrigger>
                <TabsTrigger value="optimistic" data-testid="roi-tab-optimistic">
                  Optimistic
                </TabsTrigger>
              </TabsList>
              <TabsContent value="brutal" className="mt-4" data-testid="roi-results-brutal">
                {card("brutal")}
              </TabsContent>
              <TabsContent value="base" className="mt-4" data-testid="roi-results-base">
                {card("base")}
              </TabsContent>
              <TabsContent value="optimistic" className="mt-4" data-testid="roi-results-optimistic">
                {card("optimistic")}
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Warning */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="mt-8 rounded-xl border-2 border-[--campaign-red] bg-[--campaign-red]/5 p-5 md:p-6"
          data-testid="roi-risk-warning"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-[--campaign-red] flex-none mt-0.5" />
            <div>
              <div className="font-display font-semibold">
                {t("roi.riskTitle")}
              </div>
              <p className="mt-1 text-foreground/80 leading-relaxed">
                {t("roi.risk")}
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
