/**
 * MissionParticipationDialog — Sprint 21 opt-in form for a mission.
 *
 * Opened from each mission card (via the new "Recevoir le brief" CTA).
 * Submits email + optional wallet to ``POST /api/mission-participations``;
 * backend persists the row and fires a Resend email with the AI-generated
 * mission illustration (best-effort — the form succeeds even if email
 * delivery hits a transient error).
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
import { submitMissionParticipation } from "@/lib/missionConfig";

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  missionId: string;
  missionTitle: string;
}

export function MissionParticipationDialog({
  open,
  onOpenChange,
  missionId,
  missionTitle,
}: Props): JSX.Element {
  const { t, lang } = useI18n();
  const [email, setEmail] = useState<string>("");
  const [wallet, setWallet] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    e.preventDefault();
    const v = email.trim().toLowerCase();
    if (!v || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      toast.error(
        t(
          "missionsPage.participationDialog.errorEmail",
          "Adresse email invalide."
        ) as string
      );
      return;
    }
    setSending(true);
    try {
      const ack = await submitMissionParticipation({
        mission_id: missionId,
        email: v,
        wallet_address: wallet.trim() || undefined,
        locale: lang === "en" ? "en" : "fr",
      });
      toast.success(
        t(
          "missionsPage.participationDialog.success",
          "Brief envoyé — vérifiez votre boîte de réception."
        ) as string,
        {
          description: ack.email_queued
            ? (t(
                "missionsPage.participationDialog.successQueued",
                "Le mail arrive d'ici quelques secondes."
              ) as string)
            : undefined,
        }
      );
      setEmail("");
      setWallet("");
      onOpenChange(false);
    } catch {
      toast.error(
        t(
          "missionsPage.participationDialog.errorSend",
          "Envoi impossible pour le moment. Réessayez dans un instant."
        ) as string
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-md"
        data-testid="mission-participation-dialog"
      >
        <DialogHeader>
          <DialogTitle
            className="font-display text-lg"
            data-testid="mission-participation-title"
          >
            {
              t(
                "missionsPage.participationDialog.title",
                "Recevoir le brief de la mission"
              ) as string
            }
          </DialogTitle>
          <DialogDescription>
            {
              t(
                "missionsPage.participationDialog.subtitle",
                "Un dossier classifié avec votre illustration de mission vous sera transmis par email."
              ) as string
            }
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="rounded-md border border-amber-500/30 bg-amber-500/[0.05] px-3 py-2.5">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-300/85">
              Mission
            </div>
            <div
              className="mt-1 font-display text-base text-foreground"
              data-testid="mission-participation-mission-label"
            >
              {missionTitle}
            </div>
          </div>
          <div>
            <Label
              htmlFor="mp-email"
              className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70"
            >
              Email
            </Label>
            <Input
              id="mp-email"
              type="email"
              autoComplete="email"
              required
              placeholder="agent@example.com"
              value={email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setEmail(e.target.value)
              }
              className="mt-2"
              data-testid="mission-participation-email-input"
            />
          </div>
          <div>
            <Label
              htmlFor="mp-wallet"
              className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70"
            >
              {
                t(
                  "missionsPage.participationDialog.walletLabel",
                  "Wallet Solana (optionnel)"
                ) as string
              }
            </Label>
            <Input
              id="mp-wallet"
              autoComplete="off"
              placeholder="7Xn…9f4P"
              value={wallet}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setWallet(e.target.value)
              }
              className="mt-2 font-mono text-xs"
              data-testid="mission-participation-wallet-input"
            />
          </div>
          <p className="text-[11px] text-foreground/55 leading-relaxed">
            {
              t(
                "missionsPage.participationDialog.consent",
                "En soumettant, vous acceptez de recevoir un dossier de mission par email. Désabonnement en 1 clic."
              ) as string
            }
          </p>
          <DialogFooter>
            <Button
              type="submit"
              disabled={sending}
              className="gap-2 bg-amber-500/95 hover:bg-amber-500 text-zinc-950"
              data-testid="mission-participation-submit-btn"
            >
              {sending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <Mail className="h-4 w-4" aria-hidden />
              )}
              {
                t(
                  "missionsPage.participationDialog.submitCta",
                  "Recevoir le brief"
                ) as string
              }
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
