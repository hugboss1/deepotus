/**
 * B2BInquiryDialog — modal for the white-label royaltie-25% contact form.
 */
import React, { useEffect, useState } from "react";
import { Loader2, Send } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useI18n } from "@/i18n/I18nProvider";
import { submitB2BInquiry } from "@/lib/ecosystem";

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  /** Optional pre-filled message body — used by Sprint 20.1 subscription CTA. */
  prefilledMessage?: string;
  /** Optional override for the dialog title (e.g. subscription inquiry context). */
  titleOverride?: string;
  /** Optional override for the dialog subtitle. */
  subtitleOverride?: string;
}

export function B2BInquiryDialog({
  open,
  onOpenChange,
  prefilledMessage,
  titleOverride,
  subtitleOverride,
}: Props): JSX.Element {
  const { t, lang } = useI18n();
  const [name, setName] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [company, setCompany] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);

  // When ``prefilledMessage`` changes (e.g. user opens the dialog from a
  // different subscription tier button), seed the textarea so the CTA
  // context is preserved without forcing the user to retype.
  useEffect(() => {
    if (prefilledMessage && open) {
      setMessage(prefilledMessage);
    }
  }, [prefilledMessage, open]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.error(t("ecosystem.b2b.dialog.error"));
      return;
    }
    if (message.trim().length < 10) {
      toast.error(t("ecosystem.b2b.dialog.error"));
      return;
    }
    setSending(true);
    try {
      await submitB2BInquiry({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        company: company.trim() || undefined,
        message: message.trim(),
        locale: lang === "en" ? "en" : "fr",
      });
      toast.success(t("ecosystem.b2b.dialog.success"));
      setName("");
      setEmail("");
      setCompany("");
      setMessage("");
      onOpenChange(false);
    } catch {
      toast.error(t("ecosystem.b2b.dialog.error"));
    } finally {
      setSending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="b2b-dialog">
        <DialogHeader>
          <DialogTitle>{titleOverride ?? t("ecosystem.b2b.dialog.title")}</DialogTitle>
          <DialogDescription>
            {subtitleOverride ?? t("ecosystem.b2b.dialog.subtitle")}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <Label htmlFor="b2b-name" className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70">
                {t("ecosystem.b2b.dialog.nameLabel")}
              </Label>
              <Input
                id="b2b-name"
                required
                minLength={2}
                placeholder={t("ecosystem.b2b.dialog.namePlaceholder")}
                value={name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
                className="mt-2"
                data-testid="b2b-name-input"
              />
            </div>
            <div>
              <Label htmlFor="b2b-email" className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70">
                {t("ecosystem.b2b.dialog.emailLabel")}
              </Label>
              <Input
                id="b2b-email"
                type="email"
                autoComplete="email"
                required
                placeholder={t("ecosystem.b2b.dialog.emailPlaceholder")}
                value={email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                className="mt-2"
                data-testid="b2b-email-input"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="b2b-company" className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70">
              {t("ecosystem.b2b.dialog.companyLabel")}
            </Label>
            <Input
              id="b2b-company"
              placeholder={t("ecosystem.b2b.dialog.companyPlaceholder")}
              value={company}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCompany(e.target.value)}
              className="mt-2"
              data-testid="b2b-company-input"
            />
          </div>
          <div>
            <Label htmlFor="b2b-message" className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70">
              {t("ecosystem.b2b.dialog.messageLabel")}
            </Label>
            <Textarea
              id="b2b-message"
              required
              minLength={10}
              maxLength={4000}
              rows={5}
              placeholder={t("ecosystem.b2b.dialog.messagePlaceholder")}
              value={message}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setMessage(e.target.value)}
              className="mt-2"
              data-testid="b2b-message-input"
            />
          </div>
          <DialogFooter>
            <Button
              type="submit"
              disabled={sending}
              className="gap-2 bg-cyan-500/95 hover:bg-cyan-500 text-zinc-950"
              data-testid="b2b-submit-btn"
            >
              {sending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <Send className="h-4 w-4" aria-hidden />
              )}
              {t("ecosystem.b2b.dialog.submitCta")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
