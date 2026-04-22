import React from "react";
import { useI18n } from "@/i18n/I18nProvider";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export default function FAQ() {
  const { t } = useI18n();
  const items = t("faq.items") || [];

  return (
    <section
      id="faq"
      data-testid="faq-section"
      className="py-14 sm:py-18 lg:py-24 border-t border-border"
    >
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("faq.kicker")}
        </div>
        <h2 className="mt-2 font-display text-3xl md:text-4xl font-semibold leading-tight">
          {t("faq.title")}
        </h2>

        <div className="mt-6">
          <Accordion type="single" collapsible className="w-full">
            {items.map((it, i) => (
              <AccordionItem
                key={i}
                value={`item-${i}`}
                data-testid={`faq-item-${i}`}
                className="border-border"
              >
                <AccordionTrigger className="text-left font-display font-medium text-base md:text-lg">
                  {it.q}
                </AccordionTrigger>
                <AccordionContent className="text-foreground/80 text-[15px] leading-relaxed">
                  {it.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </section>
  );
}
