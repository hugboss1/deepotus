/**
 * GenesisListDialog — modal capturing emails for the Genesis list.
 * The `source` prop tags which CTA the user came from
 * (genesis_roman / genesis_mobile) so admin can segment.
 */
import React, { useState } from "react";
import { Loader2, Mail } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useI18n } from "@/i18n/I18nProvider";
import { subscribeGenesis, type GenesisPayload } from "@/lib/ecosystem";

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  source: GenesisPayload["source"];
}

export function GenesisListDialog({ open, onOpenChange, source }: Props): JSX.Element {
  const { t, lang } = useI18n();
  const [email, setEmail] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const v = email.trim().toLowerCase();
    if (!v || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      toast.error(t("ecosystem.genesis.dialog.error"));
      return;
    }
    setSending(true);
    try {
      await subscribeGenesis({
        email: v,
        source,
        locale: lang === "en" ? "en" : "fr",
      });
      toast.success(t("ecosystem.genesis.dialog.success"));
      setEmail("");
      onOpenChange(false);
    } catch {
      toast.error(t("ecosystem.genesis.dialog.error"));
    } finally {
      setSending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" data-testid="genesis-dialog">
        <DialogHeader>
          <DialogTitle>{t("ecosystem.genesis.dialog.title")}</DialogTitle>
          <DialogDescription>
            {t("ecosystem.genesis.dialog.subtitle")}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="genesis-email" className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70">
              {t("ecosystem.genesis.dialog.emailLabel")}
            </Label>
            <Input
              id="genesis-email"
              type="email"
              autoComplete="email"
              required
              placeholder={t("ecosystem.genesis.dialog.emailPlaceholder")}
              value={email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              className="mt-2"
              data-testid="genesis-email-input"
            />
          </div>
          <p className="text-[11px] text-foreground/55 leading-relaxed">
            {t("ecosystem.genesis.dialog.consent")}
          </p>
          <DialogFooter>
            <Button
              type="submit"
              disabled={sending}
              className="gap-2 bg-amber-500/95 hover:bg-amber-500 text-zinc-950"
              data-testid="genesis-submit-btn"
            >
              {sending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <Mail className="h-4 w-4" aria-hidden />
              )}
              {t("ecosystem.genesis.dialog.submitCta")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
