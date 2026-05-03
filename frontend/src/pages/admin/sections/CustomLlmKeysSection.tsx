/**
 * CustomLlmKeysSection — Bring-Your-Own-Key vault UI for LLM providers.
 *
 * Sprint 22.3 split — extracted from the 1037-line `AdminBots.tsx` (now
 * ~700 lines after this move). Covers the full "Custom LLM keys" flow:
 *
 *   1) 3 provider cards (OpenAI / Anthropic / Gemini) with
 *      ACTIVE / NOT SET status, masked fingerprint, rotation date.
 *   2) Set / Rotate / Revoke actions.
 *   3) AES-128-GCM-aware `<Dialog>` to submit or rotate a secret; the
 *      plaintext never leaves the parent component.
 *
 * Self-contained: owns its own dialog state + secret input. The only
 * things it needs from the parent are (a) the current `bot_config`
 * snapshot (for the `custom_llm_keys._meta` + per-provider slots) and
 * (b) a callback to refresh that config after a mutation. API + auth
 * headers are injected as props, matching the pattern used by the
 * other admin sections (Loyalty, NewsFeed, AdminCadence, …).
 *
 * Behaviour parity with the old inline section is preserved 1:1 — all
 * `data-testid` attributes are unchanged so existing E2E tests keep
 * passing without modification.
 */
import { useCallback, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  KeyRound,
  Trash2,
  Eye,
  EyeOff,
  Lock as LockIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { logger } from "@/lib/logger";

/**
 * One provider slot as stored in `bot_config.custom_llm_keys.<provider>`.
 * All fields are optional because the backend only populates them once
 * a key has been set at least once.
 */
interface CustomLlmKeySlot {
  active?: boolean;
  mask?: string;
  label?: string;
  set_at?: string;
  rotated_at?: string;
}

/**
 * Shape of `bot_config.custom_llm_keys` — the 3 provider slots plus a
 * `_meta` subdoc. We type it defensively with `Partial` so a freshly
 * bootstrapped config (no keys set) doesn't trigger TS errors.
 */
interface CustomLlmKeysDoc {
  openai?: CustomLlmKeySlot;
  anthropic?: CustomLlmKeySlot;
  gemini?: CustomLlmKeySlot;
  _meta?: { kek_configured?: boolean };
}

/** Subset of `bot_config` this section cares about. */
interface BotConfigShape {
  custom_llm_keys?: CustomLlmKeysDoc;
}

type Provider = "openai" | "anthropic" | "gemini";

interface Props {
  api: string;
  headers: Record<string, string>;
  config: BotConfigShape | null;
  /**
   * Called after a successful set / rotate / revoke so the parent can
   * refresh its `bot_config` state and keep every panel in sync.
   */
  onConfigReload: () => Promise<void> | void;
}

/** Per-provider placeholder + expected prefix shown in the dialog. */
const PROVIDER_HINTS: Record<
  Provider,
  { placeholder: string; prefix: string }
> = {
  openai: { placeholder: "sk-proj-...", prefix: "sk-" },
  anthropic: { placeholder: "sk-ant-...", prefix: "sk-ant-" },
  gemini: { placeholder: "AIzaSy...", prefix: "AIza" },
};

const PROVIDERS: Provider[] = ["openai", "anthropic", "gemini"];

export default function CustomLlmKeysSection({
  api,
  headers,
  config,
  onConfigReload,
}: Props): JSX.Element {
  // The dialog is shared across the 3 providers — only one can be open
  // at a time. All state is local to this section.
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [provider, setProvider] = useState<Provider>("openai");
  const [secretInput, setSecretInput] = useState<string>("");
  const [labelInput, setLabelInput] = useState<string>("");
  const [reveal, setReveal] = useState<boolean>(false);
  const [busy, setBusy] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const openDialog = useCallback((p: Provider) => {
    setProvider(p);
    setSecretInput("");
    setLabelInput("");
    setReveal(false);
    setError(null);
    setDialogOpen(true);
  }, []);

  const submitSecret = useCallback(async () => {
    setError(null);
    const key = (secretInput || "").trim();
    if (key.length < 8) {
      setError("Key looks too short — paste the full key.");
      return;
    }
    setBusy(true);
    try {
      await axios.put(
        `${api}/api/admin/bots/llm-secrets`,
        {
          provider,
          api_key: key,
          label: (labelInput || "").trim() || undefined,
        },
        { headers },
      );
      toast.success(`${provider.toUpperCase()} key saved (encrypted)`);
      setDialogOpen(false);
      setSecretInput("");
      setLabelInput("");
      // Refetch config so the masked status updates instantly.
      await onConfigReload();
    } catch (err: unknown) {
      logger.error(err);
      // Narrow the unknown to the shape axios errors actually have.
      const axiosErr = err as {
        response?: { data?: { detail?: string } };
      };
      const msg = axiosErr?.response?.data?.detail || "Failed to save key";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  }, [api, headers, provider, secretInput, labelInput, onConfigReload]);

  const revokeSecret = useCallback(
    async (prov: Provider) => {
      if (
        !window.confirm(
          `Revoke the stored ${prov.toUpperCase()} key? The bot will fall back to the Emergent universal key on the next call.`,
        )
      ) {
        return;
      }
      try {
        await axios.delete(`${api}/api/admin/bots/llm-secrets/${prov}`, {
          headers,
        });
        toast.success(`${prov.toUpperCase()} key revoked`);
        await onConfigReload();
      } catch (err: unknown) {
        logger.error(err);
        const axiosErr = err as {
          response?: { data?: { detail?: string } };
        };
        toast.error(axiosErr?.response?.data?.detail || "Revoke failed");
      }
    },
    [api, headers, onConfigReload],
  );

  const kekConfigured = Boolean(
    config?.custom_llm_keys?._meta?.kek_configured,
  );
  const hint = PROVIDER_HINTS[provider];

  return (
    <>
      <div
        className="rounded-xl border border-border bg-card p-5 space-y-3"
        data-testid="custom-llm-keys-section"
      >
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <KeyRound size={16} className="text-[#F59E0B]" />
            <div className="font-display font-semibold">Custom LLM keys</div>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-widest"
            >
              BYO · encrypted
            </Badge>
          </div>
          {kekConfigured ? (
            <span className="font-mono text-[10px] uppercase tracking-widest text-[#18C964]">
              ✓ vault armed
            </span>
          ) : (
            <span className="font-mono text-[10px] uppercase tracking-widest text-[#E11D48]">
              ⚠ KEK not configured (ephemeral)
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Bring your own OpenAI / Anthropic / Gemini API key. Keys are
          encrypted at rest with AES-128-GCM (Fernet) using a server-only
          KEK and never returned in plaintext. When set, the bot uses your
          key directly for that provider — no silent fallback to Emergent.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {PROVIDERS.map((prov) => {
            const slot: CustomLlmKeySlot =
              config?.custom_llm_keys?.[prov] || {};
            const active = Boolean(slot.active);
            return (
              <div
                key={prov}
                className={`rounded-lg border p-3 flex flex-col gap-2 ${
                  active
                    ? "border-[#18C964]/40 bg-[#18C964]/5"
                    : "border-border bg-background/40"
                }`}
                data-testid={`custom-llm-card-${prov}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    {prov}
                  </span>
                  <span
                    className={`font-mono text-[9px] uppercase tracking-widest px-2 py-0.5 rounded-full border ${
                      active
                        ? "border-[#18C964]/50 bg-[#18C964]/10 text-[#18C964]"
                        : "border-border bg-muted text-muted-foreground"
                    }`}
                  >
                    {active ? "ACTIVE" : "NOT SET"}
                  </span>
                </div>
                <div className="font-mono text-xs text-foreground/85 truncate">
                  {active ? slot.mask || "***" : "—"}
                </div>
                {active && slot.label && (
                  <div className="text-[11px] text-muted-foreground truncate">
                    {slot.label}
                  </div>
                )}
                {active && (slot.set_at || slot.rotated_at) && (
                  <div className="font-mono text-[10px] text-muted-foreground">
                    rotated{" "}
                    {new Date(
                      slot.rotated_at || slot.set_at || "",
                    ).toLocaleDateString()}
                  </div>
                )}
                <div className="flex items-center gap-2 pt-1">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="rounded-[var(--btn-radius)] flex-1"
                    onClick={() => openDialog(prov)}
                    data-testid={`custom-llm-set-${prov}`}
                  >
                    <KeyRound size={12} className="mr-1" />
                    {active ? "Rotate" : "Set key"}
                  </Button>
                  {active && (
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="rounded-[var(--btn-radius)] text-[#E11D48] hover:text-[#E11D48]/90 hover:bg-[#E11D48]/5"
                      onClick={() => revokeSecret(prov)}
                      data-testid={`custom-llm-revoke-${prov}`}
                    >
                      <Trash2 size={12} />
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Dialog: set / rotate a custom LLM API key */}
      <Dialog
        open={dialogOpen}
        onOpenChange={(open: boolean) => {
          if (!busy) setDialogOpen(open);
        }}
      >
        <DialogContent className="sm:max-w-md" data-testid="custom-llm-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <LockIcon size={14} className="text-[#F59E0B]" />
              Set {provider.toUpperCase()} API key
            </DialogTitle>
            <DialogDescription>
              The key is encrypted at rest with AES-128-GCM and never returned
              by any GET endpoint. Only a masked fingerprint (e.g.{" "}
              <code>sk-...A1B2</code>) is shown in the UI after save.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <div>
              <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                API key
              </Label>
              <div className="relative mt-2">
                <Input
                  type={reveal ? "text" : "password"}
                  value={secretInput}
                  onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setSecretInput(e.target.value)}
                  placeholder={hint.placeholder}
                  spellCheck={false}
                  autoComplete="off"
                  className="font-mono text-xs pr-10"
                  data-testid="custom-llm-key-input"
                />
                <button
                  type="button"
                  onClick={() => setReveal((v) => !v)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={reveal ? "Hide key" : "Reveal key"}
                  data-testid="custom-llm-reveal-toggle"
                >
                  {reveal ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
                <p
                  className="mt-1 text-[10.5px] text-muted-foreground leading-relaxed"
                  data-format-hint
                >
                  Format check: must start with <code>{hint.prefix}</code>.
                  The server validates the shape before storing.
                </p>
              </div>
            </div>

            <div>
              <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                Label (optional)
              </Label>
              <Input
                value={labelInput}
                onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setLabelInput(e.target.value)}
                placeholder={`e.g. "Personal ${provider} account"`}
                className="mt-2 font-mono text-xs"
                data-testid="custom-llm-label-input"
              />
            </div>

            {error && (
              <div className="text-xs text-[#E11D48] font-mono leading-relaxed">
                {error}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={() => setDialogOpen(false)}
              className="rounded-[var(--btn-radius)]"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={submitSecret}
              disabled={busy || secretInput.length < 8}
              className="rounded-[var(--btn-radius)]"
              data-testid="custom-llm-submit"
            >
              {busy ? "Encrypting…" : "Save securely"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
