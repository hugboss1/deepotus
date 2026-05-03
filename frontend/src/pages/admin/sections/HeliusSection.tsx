import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Zap, RefreshCcw, Settings, Play } from "lucide-react";
import { logger } from "@/lib/logger";

interface HeliusWebhook {
  webhookID?: string;
  id?: string;
  webhookURL: string;
  webhookType?: string;
}

interface HeliusStatus {
  api_key_configured: boolean;
  webhook_url?: string;
  mint?: string;
  pool_address?: string;
  helius_webhooks?: HeliusWebhook[];
}

interface HeliusSectionProps {
  api: string;
  headers: { Authorization: string };
  vaultDexMode?: string | null;
  onChanged?: () => Promise<void> | void;
}

export const HeliusSection: React.FC<HeliusSectionProps> = ({
  api,
  headers,
  vaultDexMode,
  onChanged,
}) => {
  const [heliusStatus, setHeliusStatus] = useState<HeliusStatus | null>(null);
  const [heliusMint, setHeliusMint] = useState<string>("");
  const [heliusPool, setHeliusPool] = useState<string>("");
  const [heliusBusy, setHeliusBusy] = useState<boolean>(false);

  const loadHeliusStatus = async () => {
    try {
      const { data } = await axios.get(
        `${api}/api/admin/vault/helius-status`,
        { headers },
      );
      setHeliusStatus(data);
      if (heliusMint === "" && data.mint) setHeliusMint(data.mint);
      if (heliusPool === "" && data.pool_address) setHeliusPool(data.pool_address);
    } catch (e) {
      logger.error(e);
    }
  };

  const saveHeliusConfig = async () => {
    try {
      await axios.post(
        `${api}/api/admin/vault/helius-config`,
        {
          mint: heliusMint.trim() || null,
          pool_address: heliusPool.trim() || null,
        },
        { headers },
      );
      toast.success("Helius config saved");
      await loadHeliusStatus();
      if (onChanged) await onChanged();
    } catch (e: unknown) {
      // eslint-disable-next-line
      toast.error((e as any)?.response?.data?.detail || "Helius config failed");
      logger.error(e);
    }
  };

  const registerHeliusWebhook = async () => {
    setHeliusBusy(true);
    try {
      const { data } = await axios.post(
        `${api}/api/admin/vault/helius-register`,
        {
          mint: heliusMint.trim(),
          pool_address: heliusPool.trim() || null,
        },
        { headers },
      );
      toast.success(`Webhook registered · id=${data.webhook_id}`);
      await loadHeliusStatus();
      if (onChanged) await onChanged();
    } catch (e: unknown) {
      // eslint-disable-next-line
      toast.error((e as any)?.response?.data?.detail || "Helius registration failed");
      logger.error(e);
    } finally {
      setHeliusBusy(false);
    }
  };

  const runHeliusCatchup = async () => {
    setHeliusBusy(true);
    try {
      const { data } = await axios.post(
        `${api}/api/admin/vault/helius-catchup`,
        {},
        { headers },
      );
      toast.success(
        `Catch-up · ingested=${data.ingested} · buys=${data.buys} · duplicates=${data.duplicates}`,
      );
      if (onChanged) await onChanged();
    } catch (e: unknown) {
      // eslint-disable-next-line
      toast.error((e as any)?.response?.data?.detail || "Catch-up failed");
      logger.error(e);
    } finally {
      setHeliusBusy(false);
    }
  };

  const deleteHeliusWebhook = async (webhookId: string | undefined) => {
    if (!webhookId) return;
    if (!window.confirm(`Delete Helius webhook ${webhookId}?`)) return;
    try {
      await axios.delete(
        `${api}/api/admin/vault/helius-webhook/${webhookId}`,
        { headers },
      );
      toast.success("Webhook deleted");
      await loadHeliusStatus();
    } catch (e) {
      toast.error("Delete failed");
      logger.error(e);
    }
  };

  useEffect(() => {
    loadHeliusStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section
      className="mt-8 rounded-xl border border-border bg-card p-5"
      data-testid="admin-helius-section"
    >
      <div className="flex items-center gap-2 font-display font-semibold">
        <Zap
          size={16}
          className={
            heliusStatus?.api_key_configured
              ? "text-[#18C964]"
              : "text-muted-foreground"
          }
        />
        Helius · Per-Trade Indexer
        <Badge
          variant="outline"
          className={`font-mono text-[10px] uppercase ${
            heliusStatus?.api_key_configured
              ? "border-[#18C964]/50 text-[#18C964]"
              : ""
          }`}
        >
          {heliusStatus?.api_key_configured ? "API KEY OK" : "NO API KEY"}
        </Badge>
        {vaultDexMode === "helius" && (
          <Badge
            variant="outline"
            className="font-mono text-[10px] uppercase border-[#F59E0B]/50 text-[#F59E0B]"
          >
            ACTIVE SOURCE
          </Badge>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={loadHeliusStatus}
          className="ml-auto rounded-[var(--btn-radius)]"
          data-testid="admin-helius-refresh"
        >
          <RefreshCcw size={12} />
        </Button>
      </div>

      <p className="mt-2 text-xs text-muted-foreground">
        Real per-trade ingestion via Helius webhooks. When this mode is active,
        DexScreener polling is paused to avoid double-counting. Callback URL:{" "}
        <span className="font-mono">{heliusStatus?.webhook_url}</span>
      </p>

      {!heliusStatus?.api_key_configured && (
        <div className="mt-3 rounded-md border border-[#F59E0B]/40 bg-[#F59E0B]/5 p-3 text-xs text-[#F59E0B] font-mono">
          ⚠ HELIUS_API_KEY not set. Add it to backend/.env and restart the backend.
        </div>
      )}

      <div className="mt-4 grid md:grid-cols-2 gap-3">
        <div>
          <Label className="text-xs text-muted-foreground">
            $DEEPOTUS mint address
          </Label>
          <Input
            value={heliusMint}
            onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setHeliusMint(e.target.value)}
            placeholder="e.g. 9Eb2…pump"
            className="font-mono text-xs mt-1"
            data-testid="admin-helius-mint"
          />
        </div>
        <div>
          <Label className="text-xs text-muted-foreground">
            Pool LP address (optional, improves accuracy)
          </Label>
          <Input
            value={heliusPool}
            onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setHeliusPool(e.target.value)}
            placeholder="PumpSwap/Orca pool address"
            className="font-mono text-xs mt-1"
            data-testid="admin-helius-pool"
          />
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={saveHeliusConfig}
          className="rounded-[var(--btn-radius)]"
          data-testid="admin-helius-save"
        >
          <Settings size={14} className="mr-1" /> Save config
        </Button>
        <Button
          size="sm"
          onClick={registerHeliusWebhook}
          disabled={
            !heliusStatus?.api_key_configured ||
            heliusBusy ||
            !heliusMint.trim()
          }
          className="rounded-[var(--btn-radius)]"
          data-testid="admin-helius-register"
        >
          <Play size={14} className="mr-1" /> Register webhook
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={runHeliusCatchup}
          disabled={
            !heliusStatus?.api_key_configured ||
            heliusBusy ||
            !heliusMint.trim()
          }
          className="rounded-[var(--btn-radius)]"
          data-testid="admin-helius-catchup"
        >
          <RefreshCcw size={14} className="mr-1" /> Run catch-up
        </Button>
      </div>

      {heliusStatus?.helius_webhooks && heliusStatus.helius_webhooks.length > 0 && (
        <div className="mt-4">
          <div className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
            Active webhooks
          </div>
          <div className="space-y-2">
            {heliusStatus.helius_webhooks.map((w) => (
              <div
                key={w.webhookID || w.id || w.webhookURL}
                className="flex items-center justify-between rounded-md border border-border bg-background p-2 font-mono text-[11px]"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Badge variant="outline" className="font-mono text-[9px] uppercase">
                    {w.webhookType || "enhanced"}
                  </Badge>
                  <span className="truncate text-muted-foreground">
                    {w.webhookURL}
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-foreground">{w.webhookID || w.id}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteHeliusWebhook(w.webhookID || w.id)}
                    className="h-7 px-2 text-[#E11D48]"
                    data-testid={`admin-helius-delete-${w.webhookID || w.id}`}
                  >
                    ×
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 text-[11px] text-muted-foreground font-mono">
        Tip: the webhook auth header value is read from env var{" "}
        <span className="text-foreground">HELIUS_WEBHOOK_AUTH</span>. Rotate it
        there and re-register.
      </div>
    </section>
  );
};

export default HeliusSection;
