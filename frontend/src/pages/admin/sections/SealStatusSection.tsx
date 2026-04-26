import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Lock, Unlock, RefreshCcw, ShieldAlert, Bot } from "lucide-react";
import { logger } from "@/lib/logger";

interface SealStatusAdmin {
  sealed: boolean;
  mint_live: boolean;
  launch_eta: string | null;
  source: "auto" | "override";
  override: boolean | null; // null=auto · true=force sealed · false=force live
  mint: string | null;
  helius_demo_mode: boolean;
  dex_mode: string | null;
}

type ToggleValue = "auto" | "force-sealed" | "force-live";

interface SealStatusSectionProps {
  api: string;
  headers: { Authorization: string };
}

const overrideToToggle = (override: boolean | null | undefined): ToggleValue => {
  if (override === true) return "force-sealed";
  if (override === false) return "force-live";
  return "auto";
};

const toggleToOverride = (val: ToggleValue): boolean | null => {
  if (val === "force-sealed") return true;
  if (val === "force-live") return false;
  return null;
};

export const SealStatusSection: React.FC<SealStatusSectionProps> = ({
  api,
  headers,
}) => {
  const [status, setStatus] = useState<SealStatusAdmin | null>(null);
  const [busy, setBusy] = useState<boolean>(false);

  const load = async () => {
    try {
      const { data } = await axios.get(
        `${api}/api/admin/vault/classified-status`,
        { headers },
      );
      setStatus(data);
    } catch (e) {
      logger.error(e);
    }
  };

  const setOverride = async (val: ToggleValue) => {
    setBusy(true);
    try {
      const override = toggleToOverride(val);
      const { data } = await axios.post(
        `${api}/api/admin/vault/classified-status/override`,
        { override },
        { headers },
      );
      setStatus(data);
      const human =
        val === "auto"
          ? "Auto · seal status follows mint state"
          : val === "force-sealed"
          ? "Force SEALED · vault locked"
          : "Force LIVE · vault unlocked (QA)";
      toast.success(human);
    } catch (e: unknown) {
      // eslint-disable-next-line
      toast.error((e as any)?.response?.data?.detail || "Override failed");
      logger.error(e);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 15_000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const currentToggle = overrideToToggle(status?.override);
  const sealed = status?.sealed ?? true;

  return (
    <section
      className="mt-8 rounded-xl border border-border bg-card p-5"
      data-testid="admin-seal-section"
    >
      <div className="flex items-center gap-2 font-display font-semibold flex-wrap">
        {sealed ? (
          <Lock size={16} className="text-[#F59E0B]" />
        ) : (
          <Unlock size={16} className="text-[#18C964]" />
        )}
        Classified Vault · Seal Status
        <Badge
          variant="outline"
          className={`font-mono text-[10px] uppercase ${
            sealed
              ? "border-[#F59E0B]/50 text-[#F59E0B]"
              : "border-[#18C964]/50 text-[#18C964]"
          }`}
          data-testid="admin-seal-badge"
        >
          {sealed ? "SEALED" : "LIVE"}
        </Badge>
        <Badge
          variant="outline"
          className="font-mono text-[10px] uppercase tracking-widest"
          data-testid="admin-seal-source-badge"
        >
          source: {status?.source ?? "—"}
        </Badge>
        <Button
          variant="outline"
          size="sm"
          onClick={load}
          className="ml-auto rounded-[var(--btn-radius)]"
          data-testid="admin-seal-refresh"
        >
          <RefreshCcw size={12} />
        </Button>
      </div>

      <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
        Controls the <strong>real</strong> classified vault gate. When SEALED, the public TerminalPopup hides
        the Level-02 accreditation flow and only allows Genesis broadcast subscriptions (Mail #1).
        Auto-rule: <code className="font-mono">sealed = helius_demo_mode || !mint || dex_mode != "helius"</code>.
      </p>

      {/* Auto-signals snapshot */}
      <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2 font-mono text-[11px]">
        <div className="rounded-md border border-border bg-background/40 p-2">
          <div className="text-muted-foreground">helius_demo_mode</div>
          <div
            className={
              status?.helius_demo_mode
                ? "text-[#F59E0B]"
                : "text-[#18C964]"
            }
            data-testid="admin-seal-signal-demo"
          >
            {String(status?.helius_demo_mode ?? "—")}
          </div>
        </div>
        <div className="rounded-md border border-border bg-background/40 p-2">
          <div className="text-muted-foreground">dex_mode</div>
          <div
            className={
              status?.dex_mode === "helius" ? "text-[#18C964]" : "text-[#F59E0B]"
            }
            data-testid="admin-seal-signal-dexmode"
          >
            {status?.dex_mode || "—"}
          </div>
        </div>
        <div className="rounded-md border border-border bg-background/40 p-2 truncate">
          <div className="text-muted-foreground">mint</div>
          <div
            className={status?.mint ? "text-[#18C964]" : "text-[#F59E0B]"}
            data-testid="admin-seal-signal-mint"
          >
            {status?.mint
              ? `${status.mint.slice(0, 6)}…${status.mint.slice(-4)}`
              : "(unset)"}
          </div>
        </div>
      </div>

      {/* ETA */}
      {status?.launch_eta && (
        <div
          className="mt-3 rounded-md border border-[#F59E0B]/30 bg-[#F59E0B]/5 p-2 font-mono text-[11px] text-[#F59E0B]"
          data-testid="admin-seal-eta"
        >
          Genesis ETA · {new Date(status.launch_eta).toLocaleString()}
        </div>
      )}

      {/* 3-state toggle */}
      <div className="mt-4">
        <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
          Override
        </div>
        <div
          className="inline-flex items-center gap-1 rounded-[var(--btn-radius)] border border-border bg-background p-0.5"
          data-testid="admin-seal-override-toggle"
        >
          {(
            [
              { value: "auto" as ToggleValue, label: "Auto", icon: <Bot size={13} /> },
              {
                value: "force-sealed" as ToggleValue,
                label: "Force Sealed",
                icon: <Lock size={13} />,
              },
              {
                value: "force-live" as ToggleValue,
                label: "Force Live",
                icon: <Unlock size={13} />,
              },
            ]
          ).map((opt) => {
            const active = currentToggle === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                disabled={busy || active}
                onClick={() => setOverride(opt.value)}
                className={`px-3 py-1.5 rounded-[8px] font-mono text-[11px] uppercase tracking-widest transition-colors inline-flex items-center gap-1.5 ${
                  active
                    ? opt.value === "force-sealed"
                      ? "bg-[#F59E0B] text-black"
                      : opt.value === "force-live"
                      ? "bg-[#18C964] text-black"
                      : "bg-foreground text-background"
                    : "text-foreground/70 hover:text-foreground disabled:opacity-50"
                }`}
                data-testid={`admin-seal-toggle-${opt.value}`}
              >
                {opt.icon}
                {opt.label}
              </button>
            );
          })}
        </div>
        <div className="mt-2 font-mono text-[11px] text-muted-foreground inline-flex items-center gap-2">
          <ShieldAlert size={11} />
          {currentToggle === "auto" && (
            <>Auto · seal status follows on-chain signals (recommended).</>
          )}
          {currentToggle === "force-sealed" && (
            <>
              <span className="text-[#F59E0B]">Force SEALED · classified vault locked even if mint is live.</span>
            </>
          )}
          {currentToggle === "force-live" && (
            <>
              <span className="text-[#18C964]">Force LIVE · classified vault unlocked even in demo (QA only).</span>
            </>
          )}
        </div>
      </div>
    </section>
  );
};

export default SealStatusSection;
