/**
 * Tokenomics — landing page allocation breakdown orchestrator.
 *
 * Composed of three focused sub-components:
 *   - <TokenomicsChart />     : donut + gold coin + total + lock badge (left col)
 *   - <TokenomicsLegend />    : 6 allocation rows with hover highlight (right col)
 *   - <TokenomicsTaxAndBuy /> : 0% Tax Protocol block + Buy CTA block (right col)
 *
 * Owns only the shared `activeKey` cross-highlight state.
 */
import { useMemo, useState } from "react";
import { useI18n } from "@/i18n/I18nProvider";
import { ALLOCATIONS } from "./tokenomics/allocations";
import { TokenomicsChart } from "./tokenomics/TokenomicsChart";
import { TokenomicsLegend } from "./tokenomics/TokenomicsLegend";
import { TokenomicsTaxAndBuy } from "./tokenomics/TokenomicsTaxAndBuy";
import { TokenomicsCards } from "./tokenomics/TokenomicsCards";

export default function Tokenomics() {
  const { t } = useI18n();
  const [activeKey, setActiveKey] = useState(null);

  const data = useMemo(
    () =>
      ALLOCATIONS.map((a) => ({
        key: a.key,
        value: a.value,
        color: a.color,
        lockable: a.lockable,
        label: t(`tokenomics.categories.${a.key}.name`),
        detail: t(`tokenomics.categories.${a.key}.detail`),
      })),
    [t],
  );

  return (
    <section
      id="tokenomics"
      data-testid="tokenomics-chart"
      className="py-14 sm:py-18 lg:py-24 border-t border-border bg-secondary/30"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("tokenomics.kicker")}
        </div>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-3 mt-2">
          <h2 className="font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
            {t("tokenomics.title")}
          </h2>
          <div className="tabular font-mono text-sm text-muted-foreground">
            {t("tokenomics.subtitle")}
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <TokenomicsChart data={data} activeKey={activeKey} />

          <div className="lg:col-span-6">
            <TokenomicsLegend
              data={data}
              activeKey={activeKey}
              setActiveKey={setActiveKey}
            />
            <TokenomicsTaxAndBuy />
          </div>
        </div>

        <TokenomicsCards />
      </div>
    </section>
  );
}
