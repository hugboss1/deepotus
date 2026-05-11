/**
 * Transparency.tsx — Public page mounted at /transparency.
 *
 * Sprint 17.B refresh
 * -------------------
 * Same data sources as before (fully env-driven, gracefully degraded
 * pre-mint), but now organised into:
 *
 *   1. Hero block         — kicker (mono) + font-display title + tagline
 *                          aligned with the rest of the landing page
 *                          typography (same pattern as Tokenomics +
 *                          On-Chain Transparency).
 *   2. Five Wallets       — addresses, lock proofs, allocations.
 *   3. Locks shortcut     — Team + Treasury lock proof cards.
 *   4. Visualisation
 *      Carousel           — three "intelligence-grade" slides illustrated
 *                          by AI-generated screen renders:
 *                            · Distribution Cartography (BubbleMaps)
 *                            · RugCheck Live Score
 *                            · Treasury Operations Log
 *                          See <TransparencyDataCarousel/>.
 *   5. Footer disclaimer.
 *
 * Anti-patterns explicitly avoided:
 *   - No hard-coded address / URL — every address comes from
 *     ``getWallets()`` (env-driven), every URL from ``URLS.*``.
 *   - The BubbleMaps iframe is only mounted when a mint is set —
 *     pre-mint we render a placeholder tile so we never embed
 *     BubbleMaps' "no token found" error page on a trust-critical page.
 *   - RugCheck status uses the design tokens already used by the Vault
 *     (#33FF33 / #F59E0B / #FF4D4D) so the page reads as part of the
 *     same visual system.
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
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
  Flame,
  Info,
} from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import { useWalletRegistry } from "@/hooks/useWalletRegistry";
import {
  URLS,
  getWallets,
  hasMint,
  getMint,
  type WalletInfo,
} from "@/lib/launchPhase";
import ThemeToggle from "@/components/landing/ThemeToggle";
import {
  TransparencyDataCarousel,
  VIZ_SLIDE_DEFAULTS,
  type VizSlide,
} from "@/components/transparency/TransparencyDataCarousel";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

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

// Sprint 17.6 — Operation Incinerator (Proof of Scarcity)
interface ScarcityStats {
  initial_supply: number;
  total_burned: number;
  circulating_supply: number;        // raw = initial - burned
  treasury_locked: number;
  team_locked: number;
  locked_total: number;
  locked_percent: number;
  effective_circulating: number;     // the HONEST one (UI must display this)
  burn_count: number;
  burned_percent: number;
  latest_burn: {
    id: string;
    amount: number;
    tx_signature: string;
    tx_link: string;
    burned_at: string;
  } | null;
}

interface BurnFeedItem {
  id: string;
  amount: number;
  tx_signature: string;
  tx_link: string;
  burned_at: string;
  note: string | null;
  queue_item_id: string | null;
}

// Format helpers — tweet-friendly and locale-independent.
function fmtTokens(amount: number): string {
  if (amount >= 1_000_000_000) return `${(amount / 1_000_000_000).toFixed(2)}B`;
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(2)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(1)}K`;
  return amount.toLocaleString("en-US");
}

function fmtFullTokens(amount: number): string {
  return amount.toLocaleString("en-US");
}

// ---------------------------------------------------------------------
// Tokenomics share table — the public source of truth for "% of supply".
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
// RugCheck CTA (hero) — only shows once the registry has a mint address
// ---------------------------------------------------------------------
const RugCheckCta: React.FC = () => {
  const registry = useWalletRegistry();
  if (!registry.mint_live || !registry.rugcheck_url) return null;
  return (
    <div className="mt-6 flex items-center gap-3 flex-wrap" data-testid="rugcheck-cta">
      <a
        href={registry.rugcheck_url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 rounded-md border border-[#33FF33]/40 bg-[#33FF33]/10 px-4 py-2 text-xs font-mono uppercase tracking-widest text-[#33FF33] hover:bg-[#33FF33]/15 transition-colors"
        data-testid="rugcheck-cta-button"
      >
        <ShieldCheck size={14} />
        Verify on RugCheck
        <ExternalLink size={12} className="opacity-70" />
      </a>
      <span className="text-[10px] font-mono text-foreground/45 uppercase tracking-widest">
        Live contract scan · independent
      </span>
    </div>
  );
};

// ---------------------------------------------------------------------
// Five-wallets table (kept as a standalone section above the carousel)
// ---------------------------------------------------------------------
const WalletsSection: React.FC = () => {
  const { t } = useI18n();
  // Live data from the backend (with env-var fallback for SSR / first
  // paint). The hook revalidates every 30s so an admin edit shows up
  // here without forcing visitors to refresh.
  const registry = useWalletRegistry();
  const wallets = registry.wallets;
  // Slots that are *contractually* lockable — show the LOCKED/PENDING
  // badge for these even when ``lock_url`` is empty (so the public can
  // see at a glance whether the lock is still TBD).
  const LOCKABLE: ReadonlySet<string> = new Set(["team", "treasury"]);
  return (
    <section
      className="mt-12"
      data-testid="transparency-wallets-section"
    >
      <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
        {t("transparencyPage.walletsKicker") as string}
      </div>
      <div className="flex items-end justify-between gap-3 mt-2 flex-wrap">
        <h2 className="font-display text-2xl md:text-3xl lg:text-4xl font-semibold leading-tight">
          {t("transparencyPage.walletsTitle") as string}
        </h2>
        <span className="text-[10px] uppercase tracking-[0.3em] text-foreground/45 font-mono">
          5 / 5
        </span>
      </div>
      <div className="grid gap-3 mt-6">
        {wallets.map((w, idx) => {
          const lockable = LOCKABLE.has(w.id);
          const isLocked = w.lock_url.length > 0;
          return (
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
                    {lockable && isLocked && (
                      <a
                        href={w.lock_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-full border border-[#33FF33]/40 bg-[#33FF33]/8 px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest text-[#33FF33] hover:bg-[#33FF33]/15"
                        data-testid={`wallet-${w.id}-lock-badge`}
                      >
                        <Lock size={9} /> LOCKED
                        <ExternalLink size={9} className="opacity-70" />
                      </a>
                    )}
                    {lockable && !isLocked && (
                      <span
                        className="inline-flex items-center gap-1 rounded-full border border-[#F59E0B]/40 bg-[#F59E0B]/8 px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest text-[#F59E0B]"
                        data-testid={`wallet-${w.id}-pending-badge`}
                      >
                        <AlertTriangle size={9} /> PENDING
                      </span>
                    )}
                    {!lockable && isLocked && (
                      <a
                        href={w.lock_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-full border border-[#33FF33]/30 bg-[#33FF33]/5 px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest text-[#33FF33] hover:bg-[#33FF33]/10"
                        data-testid={`wallet-${w.id}-lock-badge`}
                      >
                        <Lock size={9} /> Proof
                        <ExternalLink size={9} className="opacity-70" />
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
          );
        })}
      </div>
    </section>
  );
};

// ---------------------------------------------------------------------
// Lock URL cards (team + treasury)
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
    <section className="mt-12" data-testid="transparency-locks-section">
      <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
        {t("transparencyPage.locksKicker") as string}
      </div>
      <h2 className="mt-2 font-display text-2xl md:text-3xl lg:text-4xl font-semibold leading-tight">
        {t("transparencyPage.locksTitle") as string}
      </h2>
      <div className="grid sm:grid-cols-2 gap-3 mt-6">
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
// Slide content : Distribution Cartography (BubbleMaps)
// ---------------------------------------------------------------------
const DistributionSlideContent: React.FC = () => {
  const { t } = useI18n();
  const url = URLS.bubblemaps();
  if (url) {
    return (
      <div className="rounded-md border border-foreground/15 overflow-hidden bg-black">
        <iframe
          src={url}
          title="BubbleMaps"
          width="100%"
          height="380"
          loading="lazy"
          data-testid="bubblemaps-iframe"
        />
        <div className="px-3 py-2 flex items-center justify-end gap-3 bg-foreground/[0.03]">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] font-mono uppercase tracking-widest text-[#2DD4BF] hover:underline inline-flex items-center gap-1"
          >
            Open standalone <ExternalLink size={10} />
          </a>
        </div>
      </div>
    );
  }
  return (
    <div
      className="rounded-md border border-dashed border-foreground/20 bg-foreground/[0.02] p-10 text-center text-xs text-foreground/55 font-mono uppercase tracking-widest"
      data-testid="bubblemaps-placeholder"
    >
      <MapIcon size={20} className="mx-auto mb-3 opacity-50" />
      {t("transparencyPage.bubblemapsPlaceholder") as string}
    </div>
  );
};

// ---------------------------------------------------------------------
// Slide content : RugCheck Live Score
// ---------------------------------------------------------------------
type RugStatus = "loading" | "ok" | "good" | "warning" | "danger" | "error" | "missing";

const RugCheckSlideContent: React.FC = () => {
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

  let icon = <Loader2 size={18} className="animate-spin" />;
  let badgeColor = "text-foreground/55";
  let label: string = t("transparencyPage.rugcheck.loading") as string;
  if (status === "good") {
    icon = <ShieldCheck size={18} className="text-[#33FF33]" />;
    badgeColor = "text-[#33FF33]";
    label = t("transparencyPage.rugcheck.good") as string;
  } else if (status === "warning") {
    icon = <ShieldAlert size={18} className="text-[#F59E0B]" />;
    badgeColor = "text-[#F59E0B]";
    label = t("transparencyPage.rugcheck.warning") as string;
  } else if (status === "danger") {
    icon = <ShieldAlert size={18} className="text-[#FF4D4D]" />;
    badgeColor = "text-[#FF4D4D]";
    label = t("transparencyPage.rugcheck.danger") as string;
  } else if (status === "error") {
    icon = <AlertTriangle size={18} className="text-[#F59E0B]" />;
    badgeColor = "text-[#F59E0B]";
    label = t("transparencyPage.rugcheck.error") as string;
  } else if (status === "missing") {
    label = t("transparencyPage.rugcheck.missing") as string;
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-foreground/15 bg-foreground/[0.02] p-5 flex items-center gap-4">
        {icon}
        <div className="flex-1 min-w-0">
          <div
            className={`text-sm font-mono uppercase tracking-widest ${badgeColor}`}
            data-testid="rugcheck-status"
          >
            {label}
          </div>
          {data?.score !== undefined && (
            <div className="text-[11px] font-mono uppercase tracking-widest text-foreground/45 mt-1">
              score: {data.score}
            </div>
          )}
        </div>
        {hasMint() && (
          <a
            href={URLS.rugcheck()}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] font-mono uppercase tracking-widest text-[#2DD4BF] hover:underline shrink-0 inline-flex items-center gap-1"
          >
            full report <ExternalLink size={10} />
          </a>
        )}
      </div>

      {/* MiCA-style risk explanation card */}
      <div className="rounded-md border border-foreground/15 bg-foreground/[0.02] p-4 text-xs text-foreground/70 leading-relaxed">
        {t("transparencyPage.rugcheck.note") as string}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------
// Slide content : Treasury Operations Log
// ---------------------------------------------------------------------
const OPS_TYPE_STYLES: Record<TreasuryOp["type"], { color: string; bg: string }> = {
  BUYBACK: { color: "text-[#2DD4BF]", bg: "bg-[#2DD4BF]/10" },
  DISTRIBUTION: { color: "text-[#33FF33]", bg: "bg-[#33FF33]/10" },
  BURN: { color: "text-[#FF4D4D]", bg: "bg-[#FF4D4D]/10" },
  LOCK: { color: "text-[#F59E0B]", bg: "bg-[#F59E0B]/10" },
};

const OperationsSlideContent: React.FC = () => {
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

  if (ops === null) {
    return (
      <div className="rounded-md border border-foreground/15 p-6 text-center text-foreground/55 text-xs font-mono uppercase tracking-widest">
        <Loader2 size={14} className="inline mr-2 animate-spin" />
        {t("transparencyPage.opsLoading") as string}
      </div>
    );
  }
  if (ops.length === 0) {
    return (
      <div
        className="rounded-md border border-dashed border-foreground/20 bg-foreground/[0.02] p-8 text-center text-xs text-foreground/55 font-mono uppercase tracking-widest"
        data-testid="ops-empty"
      >
        {error
          ? (t("transparencyPage.opsError") as string)
          : (t("transparencyPage.opsEmpty") as string)}
      </div>
    );
  }
  return (
    <div className="rounded-md border border-foreground/15 bg-foreground/[0.02] overflow-x-auto max-h-[420px] overflow-y-auto">
      <table className="w-full text-xs" data-testid="ops-table">
        <thead className="bg-foreground/[0.04] text-[10px] uppercase tracking-widest text-foreground/55 sticky top-0">
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
  );
};

// ---------------------------------------------------------------------
// Proof of Scarcity (Sprint 17.6 — Operation Incinerator)
// ---------------------------------------------------------------------
const ProofOfScarcityHero: React.FC = () => {
  const { t } = useI18n();
  const [stats, setStats] = useState<ScarcityStats | null>(null);
  const [burns, setBurns] = useState<BurnFeedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, b] = await Promise.all([
        axios.get<ScarcityStats>(`${API}/transparency/stats`),
        axios.get<{ items: BurnFeedItem[]; count: number }>(
          `${API}/transparency/burns?limit=5`,
        ),
      ]);
      setStats(s.data);
      setBurns(b.data?.items ?? []);
    } catch (_err) {
      setError(t("transparencyPage.scarcity.loadError") as string);
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void load();
  }, [load]);

  // Loading skeleton — keep the layout footprint stable so the Hero
  // above doesn't pop into a different vertical position when stats
  // resolve. Skeleton heights mirror the final card heights (~h-28).
  if (loading) {
    return (
      <section
        className="mt-10 border-y border-foreground/10 py-10"
        data-testid="proof-of-scarcity-loading"
      >
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] text-[#FF6B35] font-mono mb-3">
          <Flame size={14} className="animate-pulse" />
          {t("transparencyPage.scarcity.kicker") as string}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-28 rounded-md border border-foreground/10 bg-foreground/5 animate-pulse"
            />
          ))}
        </div>
      </section>
    );
  }

  if (error || !stats) {
    return (
      <section
        className="mt-10 border-y border-foreground/10 py-10 text-sm text-foreground/60"
        data-testid="proof-of-scarcity-error"
      >
        <AlertTriangle size={16} className="inline mr-2 text-[#F59E0B]" />
        {error ?? (t("transparencyPage.scarcity.loadError") as string)}
      </section>
    );
  }

  const lockedPct = stats.locked_percent.toFixed(0);
  const burnedPct = stats.burned_percent.toFixed(stats.burned_percent < 0.01 ? 4 : 2);
  const latestBurnDate = stats.latest_burn
    ? new Date(stats.latest_burn.burned_at).toLocaleString()
    : null;

  return (
    <section
      className="mt-10 border-y border-foreground/10 py-10"
      data-testid="proof-of-scarcity-section"
    >
      {/* Kicker + heading */}
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] text-[#FF6B35] font-mono">
        <Flame size={14} />
        {t("transparencyPage.scarcity.kicker") as string}
      </div>
      <h2
        className="mt-3 font-display text-2xl sm:text-3xl lg:text-4xl font-semibold leading-tight tracking-tight"
        data-testid="proof-of-scarcity-title"
      >
        {t("transparencyPage.scarcity.title") as string}
      </h2>
      <p className="mt-3 text-sm text-foreground/70 leading-relaxed max-w-2xl">
        {t("transparencyPage.scarcity.subtitle") as string}
      </p>

      {/* Three metric cards */}
      <div className="mt-7 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Initial Supply */}
        <div
          className="rounded-md border border-foreground/15 bg-foreground/[0.02] px-5 py-4"
          data-testid="scarcity-initial-card"
        >
          <p className="text-[10px] font-mono uppercase tracking-widest text-foreground/55">
            {t("transparencyPage.scarcity.initialLabel") as string}
          </p>
          <p
            className="mt-2 font-mono text-2xl sm:text-3xl font-semibold text-foreground"
            data-testid="scarcity-initial-value"
          >
            {fmtFullTokens(stats.initial_supply)}
          </p>
          <p className="mt-1 text-[10px] text-foreground/45 font-mono">
            $DEEPOTUS · Hard cap
          </p>
        </div>

        {/* Total Burned */}
        <div
          className="rounded-md border border-[#FF6B35]/30 bg-[#FF6B35]/[0.05] px-5 py-4"
          data-testid="scarcity-burned-card"
        >
          <p className="text-[10px] font-mono uppercase tracking-widest text-[#FF6B35]">
            {t("transparencyPage.scarcity.burnedLabel") as string}
          </p>
          <p
            className="mt-2 font-mono text-2xl sm:text-3xl font-semibold text-foreground flex items-baseline gap-2"
            data-testid="scarcity-burned-value"
          >
            <Flame size={20} className="text-[#FF6B35]" />
            {fmtFullTokens(stats.total_burned)}
          </p>
          <p className="mt-1 text-[10px] text-foreground/55 font-mono">
            {burnedPct}% {t("transparencyPage.scarcity.burnedPctLabel") as string}
          </p>
        </div>

        {/* Real / Effective Circulating */}
        <div
          className="rounded-md border border-[#33FF33]/30 bg-[#33FF33]/[0.04] px-5 py-4"
          data-testid="scarcity-circulating-card"
        >
          <p className="text-[10px] font-mono uppercase tracking-widest text-[#33FF33] flex items-center gap-1.5">
            {t("transparencyPage.scarcity.circulatingLabel") as string}
            <TooltipProvider delayDuration={150}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="inline-flex items-center text-foreground/55 hover:text-foreground/80 transition-colors"
                    aria-label="Disclosure"
                    data-testid="scarcity-circulating-tooltip-trigger"
                  >
                    <Info size={11} />
                  </button>
                </TooltipTrigger>
                <TooltipContent
                  side="top"
                  className="max-w-xs bg-foreground text-background text-[11px] leading-relaxed normal-case tracking-normal font-body"
                  data-testid="scarcity-circulating-tooltip"
                >
                  {t("transparencyPage.scarcity.disclaimer") as string}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </p>
          <p
            className="mt-2 font-mono text-2xl sm:text-3xl font-semibold text-foreground"
            data-testid="scarcity-circulating-value"
          >
            {fmtFullTokens(stats.effective_circulating)}
          </p>
          <p className="mt-1 text-[10px] text-foreground/55 font-mono">
            {t("transparencyPage.scarcity.circulatingHint") as string} · {lockedPct}%{" "}
            {t("transparencyPage.scarcity.lockedPctLabel") as string}
          </p>
        </div>
      </div>

      {/* Disclaimer (also visible inline, not only in tooltip — full
          mathematical honesty requires it to be readable without
          interaction). */}
      <p
        className="mt-4 text-[11px] text-foreground/55 leading-relaxed italic max-w-3xl"
        data-testid="scarcity-disclaimer-inline"
      >
        ⚖ {t("transparencyPage.scarcity.disclaimer") as string}
      </p>

      {/* Burn feed */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[11px] font-mono uppercase tracking-widest text-foreground/55">
            {t("transparencyPage.scarcity.feedTitle") as string}
          </p>
          {latestBurnDate && (
            <p className="text-[10px] font-mono text-foreground/45">
              {t("transparencyPage.scarcity.feedLatest") as string}: {latestBurnDate}
            </p>
          )}
        </div>
        {burns.length === 0 ? (
          <div
            className="rounded-md border border-dashed border-foreground/15 px-5 py-6 text-center text-xs text-foreground/55"
            data-testid="scarcity-feed-empty"
          >
            {t("transparencyPage.scarcity.feedEmpty") as string}
          </div>
        ) : (
          <ul
            className="space-y-2"
            data-testid="scarcity-feed-list"
          >
            {burns.map((b) => (
              <li
                key={b.id}
                className="rounded-md border border-foreground/10 bg-foreground/[0.02] px-4 py-3 flex items-center justify-between gap-3 flex-wrap"
                data-testid={`scarcity-burn-${b.id}`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Flame size={14} className="text-[#FF6B35] shrink-0" />
                  <div className="min-w-0">
                    <p className="font-mono text-sm font-medium text-foreground truncate">
                      {fmtTokens(b.amount)}{" "}
                      <span className="text-foreground/50 text-xs">
                        {t("transparencyPage.scarcity.feedAmount") as string}
                      </span>
                    </p>
                    <p className="text-[10px] font-mono text-foreground/45 mt-0.5">
                      {new Date(b.burned_at).toLocaleString()}
                      {b.note && <span className="ml-2 italic">· {b.note}</span>}
                    </p>
                  </div>
                </div>
                <a
                  href={b.tx_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wider text-[#33FF33] hover:text-[#22D3EE] transition-colors"
                  data-testid={`scarcity-burn-link-${b.id}`}
                >
                  {t("transparencyPage.scarcity.feedViewProof") as string}
                  <ExternalLink size={11} />
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
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

  // Compose the carousel slides — keep the data-fetching content
  // co-located with the page so VizSlide stays a dumb presentational
  // wrapper.
  const slides: VizSlide[] = useMemo(
    () =>
      VIZ_SLIDE_DEFAULTS.map((d) => {
        let content: React.ReactNode = null;
        if (d.id === "distribution") content = <DistributionSlideContent />;
        else if (d.id === "rugcheck") content = <RugCheckSlideContent />;
        else if (d.id === "operations") content = <OperationsSlideContent />;
        return { ...d, content };
      }),
    [],
  );

  return (
    <div
      className="min-h-screen bg-background text-foreground font-body"
      data-testid="transparency-page"
    >
      <header className="max-w-6xl mx-auto px-4 sm:px-6 pt-8 pb-4 flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs uppercase tracking-widest text-foreground/55 hover:text-foreground transition-colors"
          data-testid="transparency-back-link"
        >
          <ArrowLeft size={14} /> {t("common.backHome") as string}
        </Link>
        <ThemeToggle />
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pb-24">
        {/* ---- Hero ---- */}
        <section className="pt-6 border-b border-foreground/10 pb-10">
          <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-[#F59E0B]">
            {t("transparencyPage.kicker") as string}
          </p>
          <h1 className="mt-3 font-display text-4xl sm:text-5xl lg:text-6xl font-semibold leading-[1.04] tracking-tight">
            {t("transparencyPage.title") as string}
          </h1>
          <p className="mt-4 text-sm md:text-base text-foreground/75 leading-relaxed max-w-2xl">
            {t("transparencyPage.tagline") as string}
          </p>
          {mintShort && (
            <p className="mt-5 text-[10px] font-mono uppercase tracking-widest text-foreground/55">
              MINT · {mintShort}
            </p>
          )}
          {/* RugCheck CTA — only shows once the mint is in the
              registry. The button intentionally lives in the hero so
              first-touch buyers can validate the contract before any
              other on-page interaction. */}
          <RugCheckCta />
        </section>

        {/* ---- Proof of Scarcity (Sprint 17.6 — Operation Incinerator) ---- */}
        <ProofOfScarcityHero />

        {/* ---- Wallets + Locks (above the carousel) ---- */}
        <WalletsSection />
        <LocksSection />

        {/* ---- Visualisation carousel ---- */}
        <TransparencyDataCarousel slides={slides} />

        {/* ---- Footer disclaimer ---- */}
        <footer className="mt-16 border-t border-foreground/10 pt-6 text-[11px] text-foreground/50 leading-relaxed">
          {t("transparencyPage.footer") as string}
        </footer>
      </main>
    </div>
  );
};

export default Transparency;
