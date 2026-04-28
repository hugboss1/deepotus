/**
 * AccessSecuredTerminals — landing-side affiliate links section
 * (Sprint 16.3).
 *
 * Renders the "Authorized Brokerage" panel on the How-To-Buy page.
 * URLs come from `GET /api/access-terminals` so the founder can rotate
 * referral codes without a frontend redeploy. When neither BonkBot nor
 * Trojan are configured (very early bootstrap), the component renders
 * nothing — no broken buttons.
 *
 * Naming follows the user's "Access Secured Terminals" / "Authorized
 * Brokerage" lore framing — kept intentionally on-brand so the link
 * doesn't feel like a banner ad.
 */

import React, { useEffect, useState } from "react";
import axios from "axios";
import { ExternalLink, ShieldCheck, Terminal } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import { logger } from "@/lib/logger";

const API: string = process.env.REACT_APP_BACKEND_URL || "";

interface AccessTerminal {
  id: string;
  label: string;
  url: string;
  tagline: string;
  platform: string;
}

export default function AccessSecuredTerminals(): JSX.Element | null {
  const { lang } = useI18n();
  const [items, setItems] = useState<AccessTerminal[]>([]);
  const [loaded, setLoaded] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get<{ items: AccessTerminal[] }>(
          `${API}/api/access-terminals`,
        );
        if (!cancelled) {
          setItems(data.items || []);
          setLoaded(true);
        }
      } catch (err) {
        logger.debug("[access-terminals] fetch failed", err);
        if (!cancelled) setLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!loaded || items.length === 0) {
    return null;
  }

  const title =
    lang === "fr"
      ? "Terminaux sécurisés du Cabinet"
      : "Access Secured Terminals";
  const subtitle =
    lang === "fr"
      ? "Pour les agents qui préfèrent leur exécution loin des hôtels publics. Le Cabinet recommande les courtiers ci-dessous — déjà compatibles $DEEPOTUS, déjà audités par nos analystes."
      : "For agents who prefer execution off the public hotels. The Cabinet recommends the brokers below — already $DEEPOTUS-compatible, already audited by our analysts.";
  const disclosure =
    lang === "fr"
      ? "Liens d'affiliation transparents — la commission de parrainage finance le Trésor Cabinet. Aucune donnée personnelle ne quitte ce site."
      : "Transparent affiliate links — referral fees fund the Cabinet Treasury. No personal data leaves this site.";

  return (
    <section
      className="relative py-16 md:py-20"
      data-testid="access-secured-terminals"
    >
      <div className="container mx-auto max-w-5xl px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-widest text-[#F59E0B]/90 font-mono mb-3">
            <ShieldCheck size={12} />
            Authorized Brokerage · PROTOCOL ΔΣ
          </div>
          <h2 className="text-2xl md:text-3xl font-semibold text-foreground">
            {title}
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground leading-relaxed">
            {subtitle}
          </p>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((it) => (
            <a
              key={it.id}
              href={it.url}
              target="_blank"
              rel="noopener noreferrer sponsored"
              className="group block rounded-xl border border-[#F59E0B]/30 bg-[#F59E0B]/5 hover:bg-[#F59E0B]/10 px-5 py-4 transition-colors"
              data-testid={`terminal-${it.id}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="rounded-md bg-[#F59E0B]/15 text-[#F59E0B] p-2 shrink-0">
                    <Terminal size={18} />
                  </div>
                  <div className="min-w-0">
                    <div className="text-base font-semibold text-foreground truncate">
                      {it.label}
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-0.5 truncate">
                      {it.tagline}
                    </div>
                  </div>
                </div>
                <ExternalLink
                  size={14}
                  className="text-[#F59E0B]/70 mt-2 shrink-0 group-hover:text-[#F59E0B] transition-colors"
                />
              </div>
              <div className="mt-3 flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-[#F59E0B]/80">
                <span className="rounded border border-[#F59E0B]/40 px-2 py-0.5">
                  {it.platform}
                </span>
                <span className="text-muted-foreground/70 normal-case truncate">
                  {it.url.replace(/^https?:\/\//, "")}
                </span>
              </div>
            </a>
          ))}
        </div>

        {/* Disclosure */}
        <div className="mt-6 text-[10px] text-muted-foreground/70 font-mono leading-relaxed max-w-3xl">
          {disclosure}
        </div>
      </div>
    </section>
  );
}
