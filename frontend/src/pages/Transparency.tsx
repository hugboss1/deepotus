/**
 * Transparency.tsx — Public page mounted at /transparency.
 *
 * Render strategy
 * ---------------
 * Five sections, each gracefully degraded when the corresponding env
 * vars / API responses are missing. The page is meant to render
 * cleanly during pre-mint (no mint, no locks, no operations) AND
 * during live / graduated phases without any code change.
 *
 *   1. Header                  — title + tagline + back link
 *   2. Five Wallets            — addresses (or "TBD post-mint")
 *   3. Lock URLs               — Team + Treasury lock proofs
 *   4. BubbleMaps embed        — iframe (only when mint is set)
 *   5. RugCheck score          — fetch summary (only when mint is set)
 *   6. Treasury Operations Log — fetched from /api/treasury/operations
 *   7. Footer disclaimer
 *
 * Anti-patterns explicitly avoided:
 *   - We DO NOT hard-code any address / URL — every address comes from
 *     ``getWallets()`` (env-driven), every URL from ``URLS.*``.
 *   - We DO NOT render the BubbleMaps iframe before mint — embedding
 *     it with an empty ?token=… leaks BubbleMaps' "no token found"
 *     error page into our trust-critical Transparency screen.
 *   - We DO NOT colour-code RugCheck status with raw red/green hex —
 *     we reuse the design tokens already used by the Vault
 *     (#33FF33 / #F59E0B / #FF4D4D) so the page reads as part of
 *     the same visual system.
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  ArrowLeft,
  Copy,
  Check,
  ExternalLink,
  Lock,
  ShieldAlert,
  ShieldCheck,
  Loader2,
  Map as MapIcon,
  AlertTriangle,
} from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import {
  URLS,
  getWallets,
  hasMint,
  getMint,
  type WalletInfo,
} from "@/lib/launchPhase";
import ThemeToggle from "@/components/landing/ThemeToggle";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------
interface TreasuryOp {
  id: string;
  type: "BUYBACK" | "DISTRIBUTION" | "BURN" | "LOCK";
  amount_sol: number | null;
  amount_tokens: number | null;
  signature: string;
  description: string;
  wallet_from: string;
  wallet_to: string | null;
  logged_at: string;
}

interface RugCheckSummary {
  score?: number;
  risks?: Array<{ name?: string; level?: string; description?: string }>;
  // RugCheck v1 returns more fields we don't render; keep loose typing.
  // eslint-disable-next-line
  [key: string]: any;
}

// ---------------------------------------------------------------------
// Tokenomics share table — the public source of truth for "% of supply".
// Mirrors the data already used by Tokenomics.tsx but kept here as a
// const so this page doesn't import the chart component.
// ---------------------------------------------------------------------
const ALLOCATIONS: Record<WalletInfo["id"], string> = {
  deployer: "0%",
  treasury: "30%",
  team: "15%",
  creator_fees: "flux",
  community: "flux",
};

// ---------------------------------------------------------------------
// Address widget — base58 string + clipboard button + Solscan link.
// ---------------------------------------------------------------------
const AddressBlock: React.FC<{ address: string; testId?: string }> = ({
  address,
  testId,
}) => {
  const [copied, setCopied] = useState(false);
  const onCopy = useCallback(async () => {
    if (!address) return;
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      // Older browsers without clipboard API — silently no-op.
    }
  }, [address]);

  if (!address) {
    return (
      <span
        className="font-mono text-[10px] tracking-widest uppercase text-foreground/45"
        data-testid={testId ? `${testId}-tbd` : undefined}
      >
        TBD post-mint
      </span>
    );
  }

  return (
    <div className="flex items-center gap-2 min-w-0">
      <code
        className="font-mono text-[10px] sm:text-xs tracking-tight text-foreground/85 truncate flex-1"
        data-testid={testId}
      >
        {address}
      </code>
      <button
        type="button"
        onClick={onCopy}
        aria-label="Copy address"
        className="shrink-0 inline-flex items-center justify-center w-7 h-7 rounded-md border border-foreground/15 hover:border-foreground/35 hover:bg-foreground/5 transition-colors"
        data-testid={testId ? `${testId}-copy` : undefined}
      >
        {copied ? <Check size={12} className="text-[#33FF33]" /> : <Copy size={12} />}
      </button>
      <a
        href={URLS.solscanWallet(address)}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="View on Solscan"
        className="shrink-0 inline-flex items-center justify-center w-7 h-7 rounded-md border border-foreground/15 hover:border-foreground/35 hover:bg-foreground/5 transition-colors"
      >
        <ExternalLink size={12} />
      </a>
    </div>
  );
};

// ---------------------------------------------------------------------
// Five-wallets table
// ---------------------------------------------------------------------
const WalletsSection: React.FC = () => {
  const { t } = useI18n();
  const wallets = getWallets();
  return (
    <section
      className="mt-10"
      data-testid="transparency-wallets-section"
    >
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="text-lg font-semibold tracking-wide">
          {t("transparencyPage.walletsTitle") as string}
        </h2>
        <span className="text-[10px] uppercase tracking-[0.3em] text-foreground/45 font-mono">
          5 / 5
        </span>
      </div>
      <div className="grid gap-3">
        {wallets.map((w, idx) => (
          <article
            key={w.id}
            className="rounded-md border border-foreground/15 bg-foreground/[0.02] p-4 hover:border-foreground/25 transition-colors"
            data-testid={`wallet-card-${w.id}`}
          >
            <div className="flex items-start gap-4">
              <div className="shrink-0 w-8 h-8 rounded-full bg-foreground/8 flex items-center justify-center font-mono text-xs text-foreground/70">
                {idx + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <h3 className="text-sm font-semibold">
                    {t(`transparencyPage.wallets.${w.id}.name`) as string}
                  </h3>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-[#F59E0B]">
                    {ALLOCATIONS[w.id]}
                  </span>
                  {w.lockUrl && (
                    <a
                      href={w.lockUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] font-mono uppercase tracking-widest text-[#33FF33] hover:underline inline-flex items-center gap-1"
                      data-testid={`wallet-${w.id}-lock-link`}
                    >
                      <Lock size={10} /> Lock proof
                    </a>
                  )}
                </div>
                <p className="text-xs text-foreground/70 mt-1.5 leading-relaxed">
                  {t(`transparencyPage.wallets.${w.id}.purpose`) as string}
                </p>
                <div className="mt-2.5">
                  <AddressBlock address={w.address} testId={`wallet-${w.id}-address`} />
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
};

// ---------------------------------------------------------------------
// Lock URL cards (team + treasury). Shown in addition to the per-wallet
// links above to give them prominence — these are the highest-trust
// artifacts on the page.
// ---------------------------------------------------------------------
const LocksSection: React.FC = () => {
  const { t } = useI18n();
  const items = [
    { id: "team", url: URLS.teamLock, alloc: "15%", testId: "lock-team" },
    {
      id: "treasury",
      url: URLS.treasuryLock,
      alloc: "30%",
      testId: "lock-treasury",
    },
  ];
  return (
    <section className="mt-10" data-testid="transparency-locks-section">
      <h2 className="text-lg font-semibold tracking-wide mb-4">
        {t("transparencyPage.locksTitle") as string}
      </h2>
      <div className="grid sm:grid-cols-2 gap-3">
        {items.map((it) => (
          <article
            key={it.id}
            className="rounded-md border border-foreground/15 bg-foreground/[0.02] p-4"
            data-testid={`${it.testId}-card`}
          >
            <div className="flex items-start gap-3">
              <Lock
                size={14}
                className={it.url ? "text-[#33FF33]" : "text-[#F59E0B]"}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <h3 className="text-sm font-semibold capitalize">{it.id}</h3>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-foreground/45">
                    {it.alloc}
                  </span>
                </div>
                <p className="text-xs text-foreground/70 mt-1">
                  {t(`transparencyPage.locks.${it.id}.terms`) as string}
                </p>
                {it.url ? (
                  <a
                    href={it.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-2 text-xs text-[#2DD4BF] hover:underline"
                    data-testid={`${it.testId}-link`}
                  >
                    Open lock proof <ExternalLink size={12} />
                  </a>
                ) : (
                  <span
                    className="inline-flex items-center gap-1 mt-2 text-xs text-foreground/45 font-mono uppercase tracking-widest"
                    data-testid={`${it.testId}-pending`}
                  >
                    🔒 {t("transparencyPage.locks.pending") as string}
                  </span>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
};

// ---------------------------------------------------------------------
// BubbleMaps embed — only mounted when a mint is set. Otherwise we
// render a skeleton tile so the user understands the section will
// activate post-mint.
// ---------------------------------------------------------------------
const BubbleMapsSection: React.FC = () => {
  const { t } = useI18n();
  const url = URLS.bubblemaps();
  return (
    <section className="mt-10" data-testid="transparency-bubblemaps-section">
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="text-lg font-semibold tracking-wide">
          {t("transparencyPage.bubblemapsTitle") as string}
        </h2>
        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] font-mono uppercase tracking-widest text-[#2DD4BF] hover:underline"
          >
            Open standalone <ExternalLink size={10} className="inline" />
          </a>
        )}
      </div>
      {url ? (
        <iframe
          src={url}
          title="BubbleMaps"
          width="100%"
          height="600"
          loading="lazy"
          className="rounded-md border border-foreground/15"
          data-testid="bubblemaps-iframe"
        />
      ) : (
        <div
          className="rounded-md border border-dashed border-foreground/20 bg-foreground/[0.02] p-10 text-center text-xs text-foreground/55 font-mono uppercase tracking-widest"
          data-testid="bubblemaps-placeholder"
        >
          <MapIcon size={20} className="mx-auto mb-3 opacity-50" />
          {t("transparencyPage.bubblemapsPlaceholder") as string}
        </div>
      )}
    </section>
  );
};

// ---------------------------------------------------------------------
// RugCheck Live Score — fetch-on-mount, cached for the page lifetime.
// ---------------------------------------------------------------------
type RugStatus = "loading" | "ok" | "good" | "warning" | "danger" | "error" | "missing";

const RugCheckSection: React.FC = () => {
  const { t } = useI18n();
  const [status, setStatus] = useState<RugStatus>(
    hasMint() ? "loading" : "missing",
  );
  const [data, setData] = useState<RugCheckSummary | null>(null);

  useEffect(() => {
    if (!hasMint()) {
      return undefined;
    }
    let cancelled = false;
    const apiUrl = URLS.rugcheckApi();
    if (!apiUrl) {
      return undefined;
    }
    (async () => {
      try {
        const res = await axios.get(apiUrl, { timeout: 10_000 });
        if (cancelled) return;
        const score = Number((res.data as RugCheckSummary).score ?? -1);
        // RugCheck convention: lower score = lower risk. We bin into 3
        // visual tiers so the user gets a single colour at a glance.
        let s: RugStatus = "good";
        if (score >= 800) s = "danger";
        else if (score >= 400) s = "warning";
        setStatus(s);
        setData(res.data as RugCheckSummary);
      } catch {
        if (!cancelled) setStatus("error");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  let icon = <Loader2 size={16} className="animate-spin" />;
  let badgeColor = "text-foreground/55";
  let label: string = t("transparencyPage.rugcheck.loading") as string;
  if (status === "good") {
    icon = <ShieldCheck size={16} className="text-[#33FF33]" />;
    badgeColor = "text-[#33FF33]";
    label = t("transparencyPage.rugcheck.good") as string;
  } else if (status === "warning") {
    icon = <ShieldAlert size={16} className="text-[#F59E0B]" />;
    badgeColor = "text-[#F59E0B]";
    label = t("transparencyPage.rugcheck.warning") as string;
  } else if (status === "danger") {
    icon = <ShieldAlert size={16} className="text-[#FF4D4D]" />;
    badgeColor = "text-[#FF4D4D]";
    label = t("transparencyPage.rugcheck.danger") as string;
  } else if (status === "error") {
    icon = <AlertTriangle size={16} className="text-[#F59E0B]" />;
    badgeColor = "text-[#F59E0B]";
    label = t("transparencyPage.rugcheck.error") as string;
  } else if (status === "missing") {
    label = t("transparencyPage.rugcheck.missing") as string;
  }

  return (
    <section
      className="mt-10"
      data-testid="transparency-rugcheck-section"
    >
      <h2 className="text-lg font-semibold tracking-wide mb-4">
        {t("transparencyPage.rugcheckTitle") as string}
      </h2>
      <div className="rounded-md border border-foreground/15 bg-foreground/[0.02] p-4 flex items-center gap-3">
        {icon}
        <span
          className={`text-sm font-mono uppercase tracking-widest ${badgeColor}`}
          data-testid="rugcheck-status"
        >
          {label}
        </span>
        {data?.score !== undefined && (
          <span className="ml-auto text-[10px] font-mono uppercase tracking-widest text-foreground/45">
            score: {data.score}
          </span>
        )}
        {hasMint() && (
          <a
            href={URLS.rugcheck()}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] font-mono uppercase tracking-widest text-[#2DD4BF] hover:underline"
          >
            full report <ExternalLink size={10} className="inline" />
          </a>
        )}
      </div>
    </section>
  );
};

// ---------------------------------------------------------------------
// Treasury Operations Log
// ---------------------------------------------------------------------
const OPS_TYPE_STYLES: Record<TreasuryOp["type"], { color: string; bg: string }> = {
  BUYBACK: { color: "text-[#2DD4BF]", bg: "bg-[#2DD4BF]/10" },
  DISTRIBUTION: { color: "text-[#33FF33]", bg: "bg-[#33FF33]/10" },
  BURN: { color: "text-[#FF4D4D]", bg: "bg-[#FF4D4D]/10" },
  LOCK: { color: "text-[#F59E0B]", bg: "bg-[#F59E0B]/10" },
};

const OperationsSection: React.FC = () => {
  const { t } = useI18n();
  const [ops, setOps] = useState<TreasuryOp[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<{ items: TreasuryOp[] }>(
          `${API}/treasury/operations`,
          { params: { limit: 100 } },
        );
        if (!cancelled) setOps(res.data.items || []);
      } catch (err) {
        if (!cancelled) {
          setOps([]);
          setError("fetch_failed");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="mt-10" data-testid="transparency-operations-section">
      <h2 className="text-lg font-semibold tracking-wide mb-4">
        {t("transparencyPage.opsTitle") as string}
      </h2>
      {ops === null && (
        <div className="rounded-md border border-foreground/15 p-6 text-center text-foreground/55 text-xs font-mono uppercase tracking-widest">
          <Loader2 size={14} className="inline mr-2 animate-spin" />
          {t("transparencyPage.opsLoading") as string}
        </div>
      )}
      {ops !== null && ops.length === 0 && (
        <div
          className="rounded-md border border-dashed border-foreground/20 bg-foreground/[0.02] p-8 text-center text-xs text-foreground/55 font-mono uppercase tracking-widest"
          data-testid="ops-empty"
        >
          {error
            ? (t("transparencyPage.opsError") as string)
            : (t("transparencyPage.opsEmpty") as string)}
        </div>
      )}
      {ops !== null && ops.length > 0 && (
        <div className="rounded-md border border-foreground/15 bg-foreground/[0.02] overflow-x-auto">
          <table className="w-full text-xs" data-testid="ops-table">
            <thead className="bg-foreground/[0.04] text-[10px] uppercase tracking-widest text-foreground/55">
              <tr>
                <th className="text-left px-3 py-2 font-mono">Date</th>
                <th className="text-left px-3 py-2 font-mono">Type</th>
                <th className="text-left px-3 py-2 font-mono">Amount</th>
                <th className="text-left px-3 py-2 font-mono">Description</th>
                <th className="text-left px-3 py-2 font-mono">Tx</th>
              </tr>
            </thead>
            <tbody>
              {ops.map((op) => {
                const style = OPS_TYPE_STYLES[op.type];
                const date = new Date(op.logged_at).toLocaleDateString();
                const amount =
                  op.amount_tokens != null
                    ? `${op.amount_tokens.toLocaleString()} tokens`
                    : op.amount_sol != null
                      ? `${op.amount_sol.toFixed(3)} SOL`
                      : "—";
                return (
                  <tr
                    key={op.id}
                    className="border-t border-foreground/10 hover:bg-foreground/[0.03]"
                    data-testid={`op-row-${op.id}`}
                  >
                    <td className="px-3 py-2 font-mono text-[10px] text-foreground/70">
                      {date}
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-widest ${style.bg} ${style.color}`}
                      >
                        {op.type}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px]">{amount}</td>
                    <td className="px-3 py-2 text-foreground/80 max-w-[280px] truncate">
                      {op.description}
                    </td>
                    <td className="px-3 py-2">
                      <a
                        href={URLS.solscanTx(op.signature)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-mono text-[10px] text-[#2DD4BF] hover:underline inline-flex items-center gap-1"
                      >
                        {op.signature.slice(0, 6)}…{op.signature.slice(-4)}
                        <ExternalLink size={10} />
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
};

// ---------------------------------------------------------------------
// Page shell
// ---------------------------------------------------------------------
const Transparency: React.FC = () => {
  const { t } = useI18n();
  const mintShort = useMemo(() => {
    const m = getMint();
    return m ? `${m.slice(0, 6)}…${m.slice(-4)}` : null;
  }, []);

  // Sync the page title for SEO + share previews.
  useEffect(() => {
    const previous = document.title;
    document.title = `Transparency · PROTOCOL ΔΣ`;
    return () => {
      document.title = previous;
    };
  }, []);

  return (
    <div
      className="min-h-screen bg-background text-foreground font-body"
      data-testid="transparency-page"
    >
      <header className="max-w-4xl mx-auto px-4 sm:px-6 pt-8 pb-4 flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs uppercase tracking-widest text-foreground/55 hover:text-foreground transition-colors"
          data-testid="transparency-back-link"
        >
          <ArrowLeft size={14} /> {t("common.backHome") as string}
        </Link>
        <ThemeToggle />
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 pb-24">
        <section className="pt-6 border-b border-foreground/10 pb-8">
          <p className="text-[10px] font-mono uppercase tracking-[0.4em] text-[#F59E0B]">
            {t("transparencyPage.kicker") as string}
          </p>
          <h1 className="mt-3 text-3xl sm:text-4xl font-semibold tracking-tight">
            {t("transparencyPage.title") as string}
          </h1>
          <p className="mt-3 text-sm text-foreground/70 leading-relaxed max-w-2xl">
            {t("transparencyPage.tagline") as string}
          </p>
          {mintShort && (
            <p className="mt-4 text-[10px] font-mono uppercase tracking-widest text-foreground/55">
              MINT · {mintShort}
            </p>
          )}
        </section>

        <WalletsSection />
        <LocksSection />
        <BubbleMapsSection />
        <RugCheckSection />
        <OperationsSection />

        <footer className="mt-16 border-t border-foreground/10 pt-6 text-[11px] text-foreground/50 leading-relaxed">
          {t("transparencyPage.footer") as string}
        </footer>
      </main>
    </div>
  );
};

export default Transparency;
