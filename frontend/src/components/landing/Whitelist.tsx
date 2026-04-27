import React, { useState } from "react";
import axios from "axios";
import { Mail, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { useI18n } from "@/i18n/I18nProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Whitelist() {
  const { t, lang } = useI18n();
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    const v = email.trim().toLowerCase();
    if (!v || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      toast.error(t("whitelist.error"));
      return;
    }
    setSending(true);
    try {
      const res = await axios.post(`${API}/whitelist`, { email: v, lang });
      setResult(res.data);
    } catch (e) {
      toast.error(t("whitelist.error"));
    } finally {
      setSending(false);
    }
  };

  const successTemplate = t("whitelist.success") || "✓";

  return (
    <section
      id="whitelist"
      data-testid="whitelist-section"
      className="py-14 sm:py-18 lg:py-24 border-t border-border"
    >
      <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("whitelist.kicker")}
        </div>
        <h2 className="mt-2 font-display text-3xl md:text-5xl font-semibold leading-tight">
          {t("whitelist.title")}
        </h2>
        <p className="mt-3 text-foreground/80">{t("whitelist.subtitle")}</p>

        {result ? (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 inline-flex items-center gap-3 rounded-xl border-2 border-[#18C964] bg-[#18C964]/10 px-5 py-4"
            data-testid="whitelist-success-message"
          >
            <CheckCircle2 size={22} className="text-[#18C964]" />
            <span className="font-mono text-sm">
              {successTemplate.replace("__POS__", String(result.position))}
            </span>
          </motion.div>
        ) : (
          <form
            onSubmit={onSubmit}
            className="mt-8 max-w-xl mx-auto flex flex-col sm:flex-row items-stretch gap-3"
          >
            <div className="flex-1 relative">
              <Mail
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <Input
                data-testid="whitelist-email-input"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("whitelist.placeholder")}
                aria-label={t("whitelist.emailLabel")}
                className="h-12 pl-9 font-mono"
              />
            </div>
            <Button
              type="submit"
              disabled={sending}
              size="lg"
              className="rounded-[var(--btn-radius)] btn-press font-semibold"
              data-testid="whitelist-submit-button"
            >
              {sending ? "…" : t("whitelist.submit")}
            </Button>
          </form>
        )}

        <p className="mt-3 text-[11px] font-mono text-muted-foreground max-w-xl mx-auto">
          {t("whitelist.miniDisclaimer")}
        </p>
      </div>
    </section>
  );
}
