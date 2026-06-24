/**
 * Payment page (/paiement + /checkout alias).
 *
 * Two flows depending on the ``?product=`` query string:
 *
 *   * No ``?session_id``:
 *       Show a product summary (boardgame / videogen) with the current
 *       price tier (for boardgame: live counter from backend) and a
 *       'Proceed to Stripe' button. Server computes the amount; we
 *       send only ``{product_id, origin_url, locale, customer?}``.
 *
 *   * With ``?session_id``:
 *       The user just came back from Stripe. We poll
 *       ``/api/payments/checkout/status/:id`` until paid / expired /
 *       canceled / timeout, then render the appropriate confirmation
 *       state. Confirmation copy varies per product (boardgame shows
 *       founder number, videogen shows email-delivery hint).
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle2, AlertTriangle, ArrowLeft, Loader2, ShoppingBag, CreditCard, Sparkles, Package, ShoppingCart } from "lucide-react";
import TopNav from "@/components/landing/TopNav";
import Footer from "@/components/landing/Footer";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useI18n } from "@/i18n/I18nProvider";
import {
  createCheckoutSession,
  fetchBoardgameCounter,
  getCheckoutStatus,
  type BoardgameCounter,
  type CheckoutStatusOut,
  type CreateSessionPayload,
} from "@/lib/ecosystem";
import { toast } from "sonner";

type Product = "boardgame" | "videogen";
type FlowState =
  | "idle"
  | "creating"
  | "polling"
  | "paid"
  | "expired"
  | "canceled"
  | "timeout"
  | "error";

function formatEur(n: number): string {
  return n.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
}

const POLL_INTERVAL_MS = 2_000;
const POLL_MAX_ATTEMPTS = 8; // ~16s budget — webhook usually wins first

export default function Payment(): JSX.Element {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const productParam = (searchParams.get("product") as Product | null) ?? "videogen";
  const sessionId = searchParams.get("session_id");
  const canceled = searchParams.get("canceled") === "1";

  const [product, setProduct] = useState<Product>(
    productParam === "boardgame" ? "boardgame" : "videogen"
  );
  const [flow, setFlow] = useState<FlowState>("idle");
  const [counter, setCounter] = useState<BoardgameCounter | null>(null);
  const [status, setStatus] = useState<CheckoutStatusOut | null>(null);
  const [customerName, setCustomerName] = useState<string>("");
  const [customerEmail, setCustomerEmail] = useState<string>("");

  // SEO title
  useEffect(() => {
    document.title = t("payment.seo.title");
  }, [t]);

  // Pull live boardgame counter when product=boardgame
  useEffect(() => {
    if (product === "boardgame") {
      fetchBoardgameCounter()
        .then(setCounter)
        .catch((): void => undefined);
    }
  }, [product]);

  // Show canceled toast once
  useEffect(() => {
    if (canceled) {
      toast.info(t("payment.status.canceled"));
      setFlow("canceled");
      // remove the canceled flag from URL
      const next = new URLSearchParams(searchParams);
      next.delete("canceled");
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canceled]);

  // Polling loop when redirected back with ?session_id
  const pollRef = useRef<number>(0);
  useEffect((): (() => void) | undefined => {
    if (!sessionId) return undefined;
    setFlow("polling");
    let cancelled = false;
    let attempts = 0;

    const tick = async (): Promise<void> => {
      attempts++;
      pollRef.current = attempts;
      try {
        const s = await getCheckoutStatus(sessionId);
        if (cancelled) return;
        setStatus(s);
        if (s.payment_status === "paid") {
          setFlow("paid");
          return;
        }
        if (s.status === "expired") {
          setFlow("expired");
          return;
        }
        if (attempts < POLL_MAX_ATTEMPTS) {
          window.setTimeout(tick, POLL_INTERVAL_MS);
        } else {
          setFlow("timeout");
        }
      } catch {
        if (cancelled) return;
        if (attempts < POLL_MAX_ATTEMPTS) {
          window.setTimeout(tick, POLL_INTERVAL_MS);
        } else {
          setFlow("error");
        }
      }
    };
    tick();
    return (): void => {
      cancelled = true;
    };
  }, [sessionId]);

  const productLabel = useMemo(() => {
    if (product === "videogen") return t("payment.product.videogenLabel");
    return t("payment.product.boardgameLabel");
  }, [product, t]);

  const productDescription = useMemo(() => {
    if (product === "videogen") return t("payment.product.videogenDescription");
    return t("payment.product.boardgameDescription");
  }, [product, t]);

  const displayedPriceEur = useMemo(() => {
    if (product === "videogen") return 65.0;
    return counter?.current_price_eur ?? 39.99;
  }, [product, counter]);

  const startCheckout = async (): Promise<void> => {
    setFlow("creating");
    try {
      const payload: CreateSessionPayload = {
        product_id: product,
        origin_url: window.location.origin,
        locale: lang === "en" ? "en" : "fr",
        customer: {
          name: customerName.trim() || undefined,
          email: customerEmail.trim().toLowerCase() || undefined,
        },
      };
      const res = await createCheckoutSession(payload);
      window.location.href = res.url;
    } catch (e) {
      setFlow("error");
      toast.error(t("payment.status.error"));
    }
  };

  // ===== Render success / status states =====
  const renderStatusBlock = (): JSX.Element | null => {
    if (!sessionId) return null;
    if (flow === "polling" || flow === "creating") {
      return (
        <div
          className="flex items-center gap-3 rounded-xl border border-cyan-500/30 bg-cyan-500/[0.05] p-5"
          data-testid="payment-status-polling"
        >
          <Loader2 className="h-5 w-5 animate-spin text-cyan-300" aria-hidden />
          <div className="text-sm text-cyan-100/90">
            {t("payment.status.polling")}
          </div>
        </div>
      );
    }
    if (flow === "paid") {
      const orderType = status?.order?.type;
      const founderNum = status?.order?.founder_number ?? null;
      const email = status?.order?.customer?.email ?? customerEmail ?? "";
      const detailMsg =
        orderType === "videogen"
          ? t("payment.status.paidVideoGen").replace("{email}", email || "—")
          : t("payment.status.paidBoardgame").replace(
              "{number}",
              founderNum ? String(founderNum) : "—"
            );
      return (
        <div
          className="rounded-xl border border-emerald-500/35 bg-emerald-500/[0.06] p-6"
          data-testid="payment-status-paid"
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-300" aria-hidden />
            <div className="font-display font-semibold text-lg text-foreground">
              {t("payment.status.paid")}
            </div>
          </div>
          <p className="mt-3 text-sm text-foreground/80 leading-relaxed">
            {detailMsg}
          </p>
        </div>
      );
    }
    if (flow === "expired") {
      return (
        <div
          className="flex items-start gap-3 rounded-xl border border-amber-500/40 bg-amber-500/[0.06] p-5"
          data-testid="payment-status-expired"
        >
          <AlertTriangle className="h-5 w-5 text-amber-300 mt-0.5" aria-hidden />
          <div className="text-sm text-foreground/80">
            {t("payment.status.expired")}
          </div>
        </div>
      );
    }
    if (flow === "timeout") {
      return (
        <div
          className="flex items-start gap-3 rounded-xl border border-cyan-500/30 bg-cyan-500/[0.05] p-5"
          data-testid="payment-status-timeout"
        >
          <AlertTriangle className="h-5 w-5 text-cyan-300 mt-0.5" aria-hidden />
          <div className="text-sm text-foreground/80">
            {t("payment.status.timeout")}
          </div>
        </div>
      );
    }
    if (flow === "error") {
      return (
        <div
          className="flex items-start gap-3 rounded-xl border border-red-500/40 bg-red-500/[0.06] p-5"
          data-testid="payment-status-error"
        >
          <AlertTriangle className="h-5 w-5 text-red-300 mt-0.5" aria-hidden />
          <div className="text-sm text-foreground/80">
            {t("payment.status.error")}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNav />
      <main data-testid="payment-page">
        <section className="relative">
          <div
            aria-hidden
            className="absolute inset-0 -z-10"
            style={{
              background:
                "radial-gradient(50% 50% at 30% 0%, rgba(45,212,191,0.08) 0%, rgba(0,0,0,0) 70%)",
            }}
          />
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
            <div className="font-mono text-[11px] uppercase tracking-[0.32em] text-cyan-300/85">
              {t("payment.kicker")}
            </div>
            <h1 className="mt-4 font-display font-semibold text-3xl sm:text-4xl text-foreground tracking-tight">
              {t("payment.title")}
            </h1>
            <p className="mt-4 text-sm md:text-base text-foreground/70 leading-relaxed max-w-prose">
              {t("payment.lead")}
            </p>

            {/* If we're coming back from Stripe, show status block */}
            <div className="mt-8">{renderStatusBlock()}</div>

            {/* Otherwise render the product summary + Stripe button */}
            {!sessionId && (
              <div className="mt-8 rounded-2xl border border-border bg-card/50 backdrop-blur-sm p-7">
                <div className="flex items-center justify-between mb-5">
                  <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/55">
                    {t("payment.selectProduct")}
                  </div>
                  <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-[0.22em]">
                    Stripe · 3DS
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-6">
                  <button
                    type="button"
                    onClick={() => setProduct("videogen")}
                    className={`flex flex-col items-start gap-1 rounded-lg border p-3 text-left transition-colors ${
                      product === "videogen"
                        ? "border-emerald-500/50 bg-emerald-500/[0.06]"
                        : "border-border bg-background/30 hover:bg-background/60"
                    }`}
                    data-testid="payment-select-videogen"
                  >
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-3.5 w-3.5 text-emerald-300" aria-hidden />
                      <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/70">
                        Video Generator
                      </span>
                    </div>
                    <div className="font-display font-semibold text-lg tabular-nums">65,00 €</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setProduct("boardgame")}
                    className={`flex flex-col items-start gap-1 rounded-lg border p-3 text-left transition-colors ${
                      product === "boardgame"
                        ? "border-amber-500/50 bg-amber-500/[0.06]"
                        : "border-border bg-background/30 hover:bg-background/60"
                    }`}
                    data-testid="payment-select-boardgame"
                  >
                    <div className="flex items-center gap-2">
                      <Package className="h-3.5 w-3.5 text-amber-300" aria-hidden />
                      <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/70">
                        Board game
                      </span>
                    </div>
                    <div className="font-display font-semibold text-lg tabular-nums">
                      {counter ? formatEur(counter.current_price_eur) : "—"}
                    </div>
                  </button>
                </div>

                <div className="rounded-lg border border-border bg-background/40 p-4">
                  <div className="flex items-start gap-3">
                    {product === "boardgame" ? (
                      <ShoppingBag className="h-5 w-5 mt-0.5 text-amber-300" aria-hidden />
                    ) : (
                      <ShoppingCart className="h-5 w-5 mt-0.5 text-emerald-300" aria-hidden />
                    )}
                    <div className="flex-1">
                      <div
                        className="font-display font-semibold text-foreground"
                        data-testid="payment-product-label"
                      >
                        {productLabel}
                      </div>
                      <p className="mt-1 text-xs text-foreground/65 leading-relaxed font-body">
                        {productDescription}
                      </p>
                    </div>
                    <div
                      className="font-display font-bold text-2xl tabular-nums"
                      data-testid="payment-total"
                    >
                      {formatEur(displayedPriceEur)}
                    </div>
                  </div>
                </div>

                {/* Customer pre-fill */}
                <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <Label
                      htmlFor="payment-name"
                      className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70"
                    >
                      Nom
                    </Label>
                    <Input
                      id="payment-name"
                      placeholder="Votre nom"
                      value={customerName}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCustomerName(e.target.value)}
                      className="mt-2"
                      data-testid="payment-name-input"
                    />
                  </div>
                  <div>
                    <Label
                      htmlFor="payment-email"
                      className="font-mono text-[11px] uppercase tracking-[0.22em] text-foreground/70"
                    >
                      Email
                    </Label>
                    <Input
                      id="payment-email"
                      type="email"
                      autoComplete="email"
                      placeholder="vous@example.com"
                      value={customerEmail}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCustomerEmail(e.target.value)}
                      className="mt-2"
                      data-testid="payment-email-input"
                    />
                  </div>
                </div>

                <Button
                  type="button"
                  size="lg"
                  onClick={startCheckout}
                  disabled={flow === "creating"}
                  className="mt-6 w-full gap-2 bg-amber-500/95 hover:bg-amber-500 text-zinc-950 font-medium"
                  data-testid="payment-proceed-btn"
                >
                  {flow === "creating" ? (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                  ) : (
                    <CreditCard className="h-4 w-4" aria-hidden />
                  )}
                  {flow === "creating"
                    ? t("payment.status.creating")
                    : t("payment.proceed")}
                </Button>

                <p className="mt-3 text-[10px] text-foreground/55 leading-relaxed font-mono">
                  {t("payment.antiTamper")}
                </p>
              </div>
            )}

            {/* Back link */}
            <div className="mt-8">
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate("/ecosysteme")}
                className="gap-2"
                data-testid="payment-back-btn"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden />
                {t("payment.backToEcosystem")}
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
