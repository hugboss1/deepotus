/**
 * FundingFlowSection — Sprint 20 narrative section for /transparency.
 *
 * Lives at the anchor ``#funding`` so the new TopNav entry routes here.
 * Explains the two funding sources (product margins + creator fees)
 * and visualises the flow toward the 5 wallets, using the same hook
 * (useWalletRegistry) as the existing wallets section so the public
 * sees CONSISTENT data.
 */
import { ArrowRight, Banknote, Coins, ShieldCheck, Building2, Heart, ServerCog } from "lucide-react";
import { motion } from "framer-motion";
import { useI18n } from "@/i18n/I18nProvider";
import { useWalletRegistry } from "@/hooks/useWalletRegistry";

interface WalletInfo {
  id: string;
  address: string;
}

const ROLE_ICONS: Record<string, React.ElementType> = {
  deployer: ServerCog,
  treasury: Banknote,
  team: Building2,
  creator_fees: Coins,
  community: Heart,
};

function shortAddr(addr: string): string {
  if (!addr || addr.length < 12) return addr || "—";
  return `${addr.slice(0, 4)}…${addr.slice(-4)}`;
}

export function FundingFlowSection(): JSX.Element {
  const { t } = useI18n();
  const registry = useWalletRegistry();
  const wallets = (registry.wallets || []) as WalletInfo[];

  return (
    <section
      id="funding"
      data-testid="funding-flow-section"
      className="mt-16 scroll-mt-24"
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.45 }}
      >
        <div className="font-mono text-[11px] uppercase tracking-[0.32em] text-amber-400/85">
          {t("funding.kicker")}
        </div>
        <h2
          className="mt-3 font-display font-semibold text-2xl md:text-3xl lg:text-4xl text-foreground tracking-tight"
          data-testid="funding-title"
        >
          {t("funding.title")}
        </h2>
        <p className="mt-4 text-sm md:text-base text-foreground/75 leading-relaxed max-w-prose font-body">
          {t("funding.lead")}
        </p>
      </motion.div>

      {/* Two source cards */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.04] p-6">
          <div className="flex items-center gap-2 mb-2">
            <Coins className="h-4 w-4 text-amber-300" aria-hidden />
            <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-200/95">
              SOURCE 1
            </span>
          </div>
          <h3 className="font-display font-semibold text-lg text-foreground">
            {t("funding.source1.heading")}
          </h3>
          <p className="mt-2 text-sm text-foreground/75 leading-relaxed font-body">
            {t("funding.source1.body")}
          </p>
        </div>
        <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/[0.04] p-6">
          <div className="flex items-center gap-2 mb-2">
            <Banknote className="h-4 w-4 text-cyan-300" aria-hidden />
            <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-cyan-200/95">
              SOURCE 2
            </span>
          </div>
          <h3 className="font-display font-semibold text-lg text-foreground">
            {t("funding.source2.heading")}
          </h3>
          <p className="mt-2 text-sm text-foreground/75 leading-relaxed font-body">
            {t("funding.source2.body")}
          </p>
        </div>
      </div>

      {/* Flow diagram (simple SVG-free, CSS pipes) */}
      <div
        className="mt-8 rounded-xl border border-border bg-card/40 p-6"
        data-testid="funding-flow-diagram"
      >
        <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70 mb-4">
          {t("funding.flow.heading")}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          {/* Sources box */}
          <div className="rounded-md border border-border/60 bg-background/30 p-4">
            <div className="flex items-center gap-2 text-amber-300">
              <Coins className="h-4 w-4" aria-hidden />
              <span className="font-mono text-[10px] uppercase tracking-[0.22em]">IN</span>
            </div>
            <p className="mt-2 text-xs text-foreground/85 leading-relaxed font-body">
              {t("funding.flow.sources")}
            </p>
          </div>
          {/* Hub */}
          <div className="relative rounded-md border-2 border-cyan-500/40 bg-cyan-500/[0.06] p-4 text-center">
            <ArrowRight
              className="hidden md:block absolute -left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-cyan-400/80"
              aria-hidden
            />
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-cyan-200">HUB</div>
            <p className="mt-2 font-display font-semibold text-foreground">
              {t("funding.flow.hub")}
            </p>
          </div>
          {/* Outputs */}
          <div className="relative rounded-md border border-border/60 bg-background/30 p-4">
            <ArrowRight
              className="hidden md:block absolute -left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-foreground/60"
              aria-hidden
            />
            <div className="flex items-center gap-2 text-foreground/80">
              <ShieldCheck className="h-4 w-4" aria-hidden />
              <span className="font-mono text-[10px] uppercase tracking-[0.22em]">OUT</span>
            </div>
            <p className="mt-2 text-xs text-foreground/85 leading-relaxed font-body">
              {t("funding.flow.outputs")}
            </p>
          </div>
        </div>
        <p className="mt-4 text-[11px] text-foreground/55 leading-relaxed font-body italic">
          {t("funding.flow.charityNote")}
        </p>
      </div>

      {/* Wallet roles summary (compact) */}
      <div className="mt-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70 mb-4">
          {t("funding.wallets.heading")}
        </div>
        <p className="text-xs text-foreground/60 mb-5 font-body">
          {t("funding.wallets.subheading")}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {["deployer", "treasury", "team", "creator_fees", "community"].map((role) => {
            const w = wallets.find((x) => x.id === role);
            const Icon = ROLE_ICONS[role] || ShieldCheck;
            const addr = w?.address || "";
            const hasAddr = addr.length > 0;
            return (
              <div
                key={role}
                className="rounded-lg border border-border/60 bg-background/35 p-4 flex flex-col gap-2"
                data-testid={`funding-wallet-${role}`}
              >
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-foreground/70" aria-hidden />
                  <span className="font-mono text-[10px] uppercase tracking-[0.20em] text-foreground/85">
                    {t(`funding.wallets.roles.${role}.label`)}
                  </span>
                </div>
                <div className="text-xs text-foreground/70 leading-relaxed font-body">
                  {t(`funding.wallets.roles.${role}.role`)}
                </div>
                <div className="text-[11px] text-foreground/55 leading-relaxed font-body italic">
                  {t(`funding.wallets.roles.${role}.finance`)}
                </div>
                <div
                  className="mt-1 font-mono text-[11px] text-foreground/80 tabular-nums"
                  data-testid={`funding-wallet-${role}-addr`}
                >
                  {hasAddr ? shortAddr(addr) : (
                    <span className="text-amber-300/85 italic">
                      {t("funding.wallets.placeholderTitle")}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <p
        className="mt-8 text-[11px] text-foreground/55 leading-relaxed font-body italic"
        data-testid="funding-disclaimer"
      >
        {t("funding.disclaimer")}
      </p>
    </section>
  );
}
