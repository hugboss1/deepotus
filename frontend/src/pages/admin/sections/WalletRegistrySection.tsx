/**
 * WalletRegistrySection — Sprint Transparency & Trust (pre-mint).
 *
 * Operator-facing surface for the public wallet registry:
 *   1. Token Mint Address (single field; once set, drives the
 *      "Verify on RugCheck" button on /transparency).
 *   2. Five wallet slots (deployer, treasury, team, creator_fees,
 *      community), each with an address + optional lock-proof URL +
 *      friendly label.
 *
 * UX rules:
 *   * No 2FA gate — the data is metadata-only (publicly verifiable
 *     on-chain) so the friction would be net-negative.
 *   * Per-row Save button — operators are touch-typing pubkeys here
 *     and we want to fail fast if X validates wrong.
 *   * Live "LOCKED / PENDING" preview matches what /transparency
 *     will render so the operator sees exactly what the public sees.
 *   * Inline error display: the backend returns 422 with a clear
 *     ``detail`` string for any validation failure (bad base58, bad
 *     URL); we surface that next to the row that failed.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Lock,
  RefreshCcw,
  Save,
  ShieldCheck,
  Wallet as WalletIcon,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { logger } from "@/lib/logger";

const API: string = process.env.REACT_APP_BACKEND_URL || "";

// Same slot order the backend enforces — keep in lockstep with
// ``WALLET_SLOTS`` in core/wallet_registry.py.
const SLOTS: ReadonlyArray<{
  id: string;
  title: string;
  description: string;
  lockable: boolean;
}> = [
  {
    id: "deployer",
    title: "Deployer",
    description:
      "The wallet that minted $DEEPOTUS. Public for verifiability — should be empty on-chain after the launch hand-off.",
    lockable: false,
  },
  {
    id: "treasury",
    title: "Treasury",
    description:
      "Multi-sig holding the protocol reserve. Lock URL points to the Streamflow / Jupiter Lock proof.",
    lockable: true,
  },
  {
    id: "team",
    title: "Team",
    description:
      "Vested team allocation. Must be locked for ≥6 months — paste the on-chain lock receipt URL.",
    lockable: true,
  },
  {
    id: "creator_fees",
    title: "Creator Fees",
    description:
      "Wallet that collects pump.fun creator fees. Used to fund liquidity buybacks; not locked.",
    lockable: false,
  },
  {
    id: "community",
    title: "Community / Airdrop",
    description:
      "Reservoir for the Proof-of-Intelligence airdrop. Not locked but transparently tracked.",
    lockable: false,
  },
];

interface WalletRow {
  id: string;
  address: string;
  lock_url: string;
  label: string;
  updated_at?: string | null;
}

interface AdminPayload {
  wallets: WalletRow[];
  mint_address: string;
  rugcheck_url: string;
}

interface Props {
  headers: Record<string, string>;
}

// Local edit state — keyed by slot id. We don't merge into the
// fetched payload until the operator clicks Save, so a typo is
// recoverable via Reload.
type EditState = Record<string, { address: string; lock_url: string; label: string }>;

export default function WalletRegistrySection({ headers }: Props): JSX.Element {
  const [data, setData] = useState<AdminPayload | null>(null);
  const [edits, setEdits] = useState<EditState>({});
  const [busySlot, setBusySlot] = useState<string | null>(null);
  const [mintInput, setMintInput] = useState<string>("");
  const [mintBusy, setMintBusy] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorBySlot, setErrorBySlot] = useState<Record<string, string>>({});

  const reload = useCallback(async () => {
    try {
      const r = await axios.get<AdminPayload>(
        `${API}/api/admin/wallet-registry`,
        { headers },
      );
      setData(r.data);
      // Hydrate the edit state from the persisted values so per-row
      // diffs ("dirty?") work cleanly.
      const next: EditState = {};
      r.data.wallets.forEach((w) => {
        next[w.id] = {
          address: w.address,
          lock_url: w.lock_url,
          label: w.label,
        };
      });
      setEdits(next);
      setMintInput(r.data.mint_address);
      setErrorBySlot({});
    } catch (err: unknown) {
      logger.error(err);
      toast.error("Failed to load wallet registry");
    } finally {
      setLoading(false);
    }
  }, [headers]);

  useEffect(() => {
    reload();
  }, [reload]);

  // Quick lookup of "what's in Mongo for slot X" so the dirty flag works.
  const persistedById = useMemo(() => {
    const map: Record<string, WalletRow> = {};
    (data?.wallets || []).forEach((w) => {
      map[w.id] = w;
    });
    return map;
  }, [data]);

  const setEdit = (slot: string, field: keyof EditState[string], v: string) => {
    setEdits((prev) => ({
      ...prev,
      [slot]: { ...(prev[slot] || { address: "", lock_url: "", label: "" }), [field]: v },
    }));
  };

  const isDirty = (slot: string): boolean => {
    const e = edits[slot];
    const p = persistedById[slot];
    if (!e) return false;
    return (
      e.address !== (p?.address || "") ||
      e.lock_url !== (p?.lock_url || "") ||
      e.label !== (p?.label || "")
    );
  };

  const saveSlot = async (slot: string) => {
    const e = edits[slot];
    if (!e) return;
    setBusySlot(slot);
    setErrorBySlot((prev) => {
      const next = { ...prev };
      delete next[slot];
      return next;
    });
    try {
      await axios.put(
        `${API}/api/admin/wallet-registry/${slot}`,
        { address: e.address, lock_url: e.lock_url, label: e.label },
        { headers },
      );
      toast.success(`${slot.replace("_", " ")} saved`);
      await reload();
    } catch (err: unknown) {
      logger.error(err);
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Save failed";
      setErrorBySlot((prev) => ({ ...prev, [slot]: detail }));
      toast.error(detail);
    } finally {
      setBusySlot(null);
    }
  };

  const saveMint = async () => {
    setMintBusy(true);
    try {
      await axios.put(
        `${API}/api/admin/wallet-registry/mint-address`,
        { address: mintInput.trim() },
        { headers },
      );
      toast.success(mintInput.trim() ? "Mint address saved" : "Mint address cleared");
      await reload();
    } catch (err: unknown) {
      logger.error(err);
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Save failed";
      toast.error(detail);
    } finally {
      setMintBusy(false);
    }
  };

  if (loading) {
    return (
      <div
        className="font-mono text-sm text-muted-foreground py-10 text-center"
        data-testid="wallet-registry-loading"
      >
        <Loader2 className="inline-block animate-spin mr-2" size={14} />
        Loading wallet registry…
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="wallet-registry-section">
      {/* ============== TOKEN MINT ADDRESS ============== */}
      <section
        className="rounded-xl border border-border bg-card p-5 space-y-3"
        data-testid="mint-address-section"
      >
        <header className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <ShieldCheck size={16} className="text-[#22D3EE]" />
            <h3 className="font-display font-semibold">Token Mint Address</h3>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-widest"
            >
              Public · pre-mint critical
            </Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={reload}
            className="rounded-[var(--btn-radius)]"
            data-testid="wallet-registry-refresh"
          >
            <RefreshCcw size={12} className="mr-1" /> Refresh
          </Button>
        </header>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Paste the canonical $DEEPOTUS mint address as soon as the
          token is deployed on pump.fun. Once set, /transparency
          surfaces the <strong>"Verify on RugCheck"</strong> button and
          unlocks BubbleMaps embedding.
        </p>
        <div className="flex flex-col md:flex-row md:items-end gap-3">
          <div className="flex-1 min-w-0">
            <Label className="text-xs text-muted-foreground uppercase tracking-widest">
              Mint address (base58, 32–44 chars)
            </Label>
            <Input
              value={mintInput}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMintInput(e.target.value)}
              placeholder="e.g. 9aBcD…XyZpump"
              className="mt-2 font-mono text-xs"
              spellCheck={false}
              autoComplete="off"
              data-testid="mint-address-input"
            />
          </div>
          <Button
            type="button"
            onClick={saveMint}
            disabled={mintBusy || mintInput.trim() === (data?.mint_address || "")}
            className="rounded-[var(--btn-radius)]"
            data-testid="mint-address-save"
          >
            <Save size={12} className="mr-1" />
            {mintBusy ? "Saving…" : "Save"}
          </Button>
        </div>
        {data?.mint_address ? (
          <div className="flex items-center justify-between gap-3 rounded-md border border-[#18C964]/30 bg-[#18C964]/5 px-3 py-2 flex-wrap">
            <div className="flex items-center gap-2 min-w-0">
              <CheckCircle2 size={14} className="text-[#18C964] flex-shrink-0" />
              <span className="font-mono text-xs text-[#18C964]">MINT LIVE</span>
              <span className="font-mono text-xs text-foreground/85 truncate">
                {data.mint_address}
              </span>
            </div>
            <a
              href={data.rugcheck_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-mono text-[#22D3EE] hover:text-[#22D3EE]/80"
              data-testid="mint-rugcheck-link"
            >
              <ExternalLink size={11} /> Verify on RugCheck
            </a>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-md border border-[#F59E0B]/30 bg-[#F59E0B]/5 px-3 py-2">
            <AlertTriangle size={14} className="text-[#F59E0B] flex-shrink-0" />
            <span className="font-mono text-xs text-[#F59E0B]">
              MINT PENDING — set after pump.fun deploy.
            </span>
          </div>
        )}
      </section>

      <Separator />

      {/* ============== PUBLIC WALLETS ============== */}
      <section
        className="rounded-xl border border-border bg-card p-5 space-y-3"
        data-testid="wallets-registry"
      >
        <header className="flex items-center gap-2">
          <WalletIcon size={16} className="text-[#F59E0B]" />
          <h3 className="font-display font-semibold">Public Wallets ({SLOTS.length})</h3>
          <Badge
            variant="outline"
            className="font-mono text-[10px] uppercase tracking-widest"
          >
            Transparency · MiCA
          </Badge>
        </header>
        <p className="text-xs text-muted-foreground leading-relaxed">
          The five wallets disclosed on /transparency. Each address is
          publicly verifiable on Solscan; the lock URL is what proves
          tokens are time-locked. Empty <code className="font-mono">lock_url</code>{" "}
          → orange <strong>PENDING</strong> badge. Filled → green{" "}
          <strong>LOCKED</strong> badge linking to the proof.
        </p>

        <div className="space-y-3">
          {SLOTS.map((slot) => {
            const e = edits[slot.id] || { address: "", lock_url: "", label: "" };
            const persisted = persistedById[slot.id];
            const dirty = isDirty(slot.id);
            const lockState = (persisted?.lock_url || "").length > 0 ? "locked" : "pending";
            const slotErr = errorBySlot[slot.id];
            return (
              <div
                key={slot.id}
                className="rounded-lg border border-border bg-background/40 p-4 space-y-3"
                data-testid={`wallet-row-${slot.id}`}
              >
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-display font-semibold uppercase tracking-widest text-sm">
                      {slot.title}
                    </span>
                    {slot.lockable && (
                      <span
                        className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[9px] uppercase tracking-widest ${
                          lockState === "locked"
                            ? "border-[#18C964]/50 bg-[#18C964]/10 text-[#18C964]"
                            : "border-[#F59E0B]/50 bg-[#F59E0B]/10 text-[#F59E0B]"
                        }`}
                        data-testid={`wallet-row-${slot.id}-badge`}
                      >
                        {lockState === "locked" ? (
                          <>
                            <Lock size={9} /> LOCKED
                          </>
                        ) : (
                          <>
                            <AlertTriangle size={9} /> PENDING
                          </>
                        )}
                      </span>
                    )}
                  </div>
                  {dirty && (
                    <span className="font-mono text-[10px] text-[#F59E0B]">
                      <AlertTriangle size={10} className="inline-block mr-1" />
                      unsaved
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  {slot.description}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                      Public Address
                    </Label>
                    <Input
                      value={e.address}
                      onChange={(ev: React.ChangeEvent<HTMLInputElement>) =>
                        setEdit(slot.id, "address", ev.target.value)
                      }
                      placeholder="base58 pubkey…"
                      spellCheck={false}
                      autoComplete="off"
                      className="mt-2 font-mono text-xs"
                      data-testid={`wallet-row-${slot.id}-address`}
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                      Lock Verification URL{slot.lockable ? "" : " (optional)"}
                    </Label>
                    <Input
                      value={e.lock_url}
                      onChange={(ev: React.ChangeEvent<HTMLInputElement>) =>
                        setEdit(slot.id, "lock_url", ev.target.value)
                      }
                      placeholder="https://streamflow.finance/contract/…"
                      spellCheck={false}
                      autoComplete="off"
                      className="mt-2 font-mono text-xs"
                      data-testid={`wallet-row-${slot.id}-lock`}
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                    Friendly Label (optional)
                  </Label>
                  <Input
                    value={e.label}
                    onChange={(ev: React.ChangeEvent<HTMLInputElement>) =>
                      setEdit(slot.id, "label", ev.target.value)
                    }
                    placeholder='e.g. "3-of-5 Multi-sig"'
                    className="mt-2 font-mono text-xs"
                    data-testid={`wallet-row-${slot.id}-label`}
                  />
                </div>
                {slotErr && (
                  <div
                    className="flex items-center gap-2 rounded-md border border-[#E11D48]/40 bg-[#E11D48]/5 px-3 py-2 text-xs font-mono text-[#E11D48]"
                    data-testid={`wallet-row-${slot.id}-error`}
                  >
                    <XCircle size={12} />
                    {slotErr}
                  </div>
                )}
                <div className="flex items-center justify-end gap-2 flex-wrap">
                  {persisted?.address && (
                    <a
                      href={`https://solscan.io/account/${persisted.address}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-mono text-[#22D3EE] hover:text-[#22D3EE]/80 mr-auto"
                      data-testid={`wallet-row-${slot.id}-solscan`}
                    >
                      <ExternalLink size={11} /> Solscan
                    </a>
                  )}
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => saveSlot(slot.id)}
                    disabled={!dirty || busySlot === slot.id}
                    className="rounded-[var(--btn-radius)]"
                    data-testid={`wallet-row-${slot.id}-save`}
                  >
                    <Save size={12} className="mr-1" />
                    {busySlot === slot.id ? "Saving…" : "Save"}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
