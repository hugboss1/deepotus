/**
 * LoyaltySection — Bots Control admin panel for the loyalty engine.
 *
 * Self-contained: owns its own state + API calls. Parent only renders
 * `<LoyaltySection api={API} headers={headers} />`. Extracted from the
 * 2700-line AdminBots.jsx (Sprint 5 split phase).
 *
 * Powers two flows:
 *   - Vault-aware loyalty hints injected into Prophet bot LLM prompts.
 *   - Loyalty email #3 sent to Niveau-02 holders after a configurable delay.
 *
 * Behaviour parity with the old inline section is preserved 1:1; the
 * data-testids are unchanged so existing E2E tests keep passing.
 */
import { useCallback, useEffect, useState } from "react";
import axios from "axios";
// Sprint 22 — `AxiosRequestHeaders` was too strict for our useMemo header object.
import { RefreshCw, Newspaper, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import type {
  LoyaltyEmailStats,
  LoyaltyStatus,
  LoyaltyTestSendResult,
} from "@/types";

interface LoyaltyPatchBody {
  hints_enabled?: boolean;
  email_enabled?: boolean;
  email_delay_hours?: number;
}

interface Props {
  api: string;
  headers: Record<string, string>;
}

export default function LoyaltySection({ api, headers }: Props) {
  const [loyalty, setLoyalty] = useState<LoyaltyStatus | null>(null);
  const [emailStats, setEmailStats] = useState<LoyaltyEmailStats | null>(null);
  const [busy, setBusy] = useState(false);
  const [testEmail, setTestEmail] = useState("");
  const [testAccred, setTestAccred] = useState("");
  const [testBusy, setTestBusy] = useState(false);
  const [testResult, setTestResult] = useState<LoyaltyTestSendResult | null>(
    null,
  );

  const load = useCallback(async () => {
    try {
      const [{ data: l }, statsRes] = await Promise.all([
        axios.get<LoyaltyStatus>(`${api}/api/admin/bots/loyalty`, { headers }),
        axios
          .get<LoyaltyEmailStats>(
            `${api}/api/admin/bots/loyalty/email-stats`,
            { headers },
          )
          .catch(() => ({ data: null as LoyaltyEmailStats | null })),
      ]);
      setLoyalty(l);
      setEmailStats(statsRes?.data ?? null);
    } catch (err) {
      logger.error(err);
    }
  }, [api, headers]);

  useEffect(() => {
    load();
  }, [load]);

  async function patch(body: LoyaltyPatchBody) {
    setBusy(true);
    try {
      await axios.put(
        `${api}/api/admin/bots/config`,
        { loyalty: body },
        { headers },
      );
      await load();
      toast.success("Loyalty config updated");
    } catch (err) {
      logger.error(err);
      toast.error("Could not update loyalty config");
    } finally {
      setBusy(false);
    }
  }

  async function sendTest() {
    const email = (testEmail || "").trim();
    if (!email) {
      toast.error("Email required for force-send");
      return;
    }
    setTestBusy(true);
    setTestResult(null);
    try {
      const { data } = await axios.post<LoyaltyTestSendResult>(
        `${api}/api/admin/bots/loyalty/test-send`,
        {
          email,
          accreditation_number: (testAccred || "").trim() || undefined,
        },
        { headers },
      );
      setTestResult(data);
      if (data?.status === "sent") {
        toast.success(`Loyalty email sent to ${email}`);
        await load();
      } else {
        toast.error(`Send status: ${data?.status || "unknown"}`);
      }
    } catch (err) {
      logger.error(err);
      toast.error("Force-send failed");
    } finally {
      setTestBusy(false);
    }
  }

  return (
    <div
      className="rounded-xl border border-border bg-card p-5 space-y-4"
      data-testid="loyalty-section"
    >
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-[#2DD4BF]" />
          <div className="font-display font-semibold">
            Loyalty engine · vault-aware hints
          </div>
          <Badge
            variant="outline"
            className="font-mono text-[10px] uppercase tracking-widest"
            data-testid="loyalty-current-tier"
          >
            {loyalty?.current_tier || "—"} ·{" "}
            {loyalty?.progress_percent != null
              ? `${loyalty.progress_percent}%`
              : "—"}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={load}
          disabled={busy}
          data-testid="loyalty-refresh-btn"
        >
          <RefreshCw size={14} className="mr-1.5" /> Refresh
        </Button>
      </div>

      <p className="text-xs text-muted-foreground leading-relaxed">
        When enabled, the Prophet bot studio will inject a tier-aware
        &quot;stay-loyal&quot; hint into every LLM prompt — escalating the
        signal as the Vault fills (5 tiers · 0-25 silent · 25-50 subtle ·
        50-75 explicit · 75-90 loud · 90+ reward). Hints never name a future
        token and never promise a date or amount.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <ToggleRow
          label="Inject in bot posts"
          subKey="hints_enabled"
          checked={!!loyalty?.hints_enabled}
          disabled={busy}
          onChange={(v) => patch({ hints_enabled: v })}
          testId="loyalty-hints-toggle"
        />
        <ToggleRow
          label="Loyalty email #3"
          subKey="email_enabled"
          checked={!!loyalty?.email_enabled}
          disabled={busy}
          onChange={(v) => patch({ email_enabled: v })}
          testId="loyalty-email-toggle"
        />
        <div className="rounded-lg border border-border bg-secondary/30 p-3 flex items-center justify-between gap-2">
          <div>
            <div className="text-xs font-medium">Email delay</div>
            <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest">
              hours after Niveau 02
            </div>
          </div>
          <Input
            type="number"
            min={1}
            max={168}
            step={1}
            value={loyalty?.email_delay_hours ?? 12}
            onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
              setLoyalty((prev) =>
                prev
                  ? { ...prev, email_delay_hours: Number(e.target.value || 12) }
                  : prev,
              )
            }
            onBlur={(e: React.FocusEvent<HTMLInputElement>) =>
              patch({
                email_delay_hours: Math.max(
                  1,
                  Math.min(168, Number(e.target.value || 12)),
                ),
              })
            }
            className="w-20 text-right font-mono text-sm"
            data-testid="loyalty-email-delay-input"
          />
        </div>
      </div>

      <div
        className="rounded-lg border border-border bg-[#0B0D10]/85 text-white p-3"
        data-testid="loyalty-active-preview"
      >
        <div className="font-mono text-[10px] uppercase tracking-widest text-white/60 mb-1.5">
          Active hint at {loyalty?.progress_percent ?? 0}% (tier ={" "}
          <span className="text-[#2DD4BF]">
            {loyalty?.current_tier || "—"}
          </span>
          )
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <SampleHint lang="FR" text={loyalty?.sample_hint_fr || null} />
          <SampleHint lang="EN" text={loyalty?.sample_hint_en || null} />
        </div>
      </div>

      <EmailDispatchPanel
        emailStats={emailStats}
        testEmail={testEmail}
        setTestEmail={setTestEmail}
        testAccred={testAccred}
        setTestAccred={setTestAccred}
        testBusy={testBusy}
        onSendTest={sendTest}
        testResult={testResult}
      />

      <details
        className="rounded-lg border border-border bg-secondary/30 p-3"
        data-testid="loyalty-tiers-details"
      >
        <summary className="text-xs font-medium cursor-pointer">
          All tiers ({loyalty?.tiers?.length || 0})
        </summary>
        <div className="mt-3 space-y-2">
          {(loyalty?.tiers || []).map((tier) => (
            <TierRow key={tier.tier} tier={tier} />
          ))}
        </div>
      </details>
    </div>
  );
}

// ---------------------------------------------------------------------
// Sub-components — kept private to this module to keep the public API
// surface narrow and dependency tree simple.
// ---------------------------------------------------------------------
interface ToggleRowProps {
  label: string;
  subKey: string;
  checked: boolean;
  disabled: boolean;
  onChange: (v: boolean) => void;
  testId: string;
}

function ToggleRow({
  label,
  subKey,
  checked,
  disabled,
  onChange,
  testId,
}: ToggleRowProps) {
  return (
    <div className="rounded-lg border border-border bg-secondary/30 p-3 flex items-center justify-between">
      <div>
        <div className="text-xs font-medium">{label}</div>
        <div className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest">
          {subKey}
        </div>
      </div>
      <Switch
        checked={checked}
        disabled={disabled}
        onCheckedChange={onChange}
        data-testid={testId}
      />
    </div>
  );
}

function SampleHint({ lang, text }: { lang: "FR" | "EN"; text: string | null }) {
  return (
    <div className="rounded-md border border-white/10 px-2 py-1.5">
      <div className="text-[9px] text-white/50 font-mono uppercase tracking-widest">
        {lang}
      </div>
      <div className="text-xs text-white/90 italic">
        “{text || "— silent —"}”
      </div>
    </div>
  );
}

function TierRow({ tier }: { tier: LoyaltyStatus["tiers"][number] }) {
  return (
    <div
      className="rounded-md border border-border bg-card p-2.5"
      data-testid={`loyalty-tier-${tier.tier}`}
    >
      <div className="flex items-center gap-2 flex-wrap">
        <Badge
          variant="outline"
          className="font-mono text-[10px] uppercase tracking-widest"
        >
          {tier.tier}
        </Badge>
        <span className="font-mono text-[10px] text-muted-foreground">
          {tier.lower_pct}% – {tier.upper_pct}%
        </span>
      </div>
      {tier.hints_fr.length > 0 && (
        <ul className="mt-1.5 ml-4 list-disc text-[11px] text-muted-foreground space-y-0.5">
          {tier.hints_fr.map((h: string, i: number) => (
            <li key={`fr-${i}`}>
              <span className="font-mono text-[9px] text-[#F59E0B] mr-1">FR</span>
              {h}
            </li>
          ))}
          {tier.hints_en.map((h: string, i: number) => (
            <li key={`en-${i}`}>
              <span className="font-mono text-[9px] text-[#2DD4BF] mr-1">EN</span>
              {h}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

interface EmailPanelProps {
  emailStats: LoyaltyEmailStats | null;
  testEmail: string;
  setTestEmail: (s: string) => void;
  testAccred: string;
  setTestAccred: (s: string) => void;
  testBusy: boolean;
  onSendTest: () => void;
  testResult: LoyaltyTestSendResult | null;
}

function EmailDispatchPanel({
  emailStats,
  testEmail,
  setTestEmail,
  testAccred,
  setTestAccred,
  testBusy,
  onSendTest,
  testResult,
}: EmailPanelProps) {
  return (
    <div
      className="rounded-lg border border-border bg-secondary/30 p-3 space-y-3"
      data-testid="loyalty-email-panel"
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <Newspaper size={14} className="text-[#F59E0B]" />
          <span className="text-xs font-medium">
            Loyalty email · dispatch stats
          </span>
        </div>
        <div className="flex items-center gap-2 flex-wrap font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          <span data-testid="loyalty-email-total-sent">
            sent={emailStats?.total_sent ?? 0}
          </span>
          <span>·</span>
          <span data-testid="loyalty-email-pending-now">
            pending={emailStats?.pending_now ?? 0}
          </span>
          {emailStats?.last_sent_at && (
            <>
              <span>·</span>
              <span data-testid="loyalty-email-last-sent">
                last={emailStats.last_sent_at.slice(0, 16)}
              </span>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <Input
          type="email"
          placeholder="email@example.com"
          value={testEmail}
          onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setTestEmail(e.target.value)}
          className="text-sm"
          data-testid="loyalty-test-email-input"
        />
        <Input
          type="text"
          placeholder="ACCRED-XXXX (optional)"
          value={testAccred}
          onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setTestAccred(e.target.value)}
          className="text-sm font-mono"
          data-testid="loyalty-test-accred-input"
        />
        <Button
          onClick={onSendTest}
          disabled={testBusy || !testEmail}
          data-testid="loyalty-test-send-btn"
          className="font-mono uppercase tracking-widest text-xs"
        >
          {testBusy ? "Sending…" : "Force-send now"}
        </Button>
      </div>

      {testResult && (
        <div
          className="rounded-md border border-border bg-card p-2.5 font-mono text-[11px] space-y-1"
          data-testid="loyalty-test-result"
        >
          <div className="flex items-center justify-between">
            <span className="uppercase tracking-widest text-muted-foreground">
              status
            </span>
            <Badge
              variant={testResult.status === "sent" ? "default" : "outline"}
              className="text-[10px] uppercase"
            >
              {testResult.status}
            </Badge>
          </div>
          {testResult.email_id && (
            <div className="text-muted-foreground break-all">
              id: {testResult.email_id}
            </div>
          )}
          {testResult.error && (
            <div className="text-destructive">{testResult.error}</div>
          )}
          {testResult.prophet_message && (
            <details className="mt-1">
              <summary className="cursor-pointer text-[10px] uppercase tracking-widest text-muted-foreground">
                Prophet message preview
              </summary>
              <div className="mt-1 italic text-foreground/90 leading-relaxed">
                {testResult.prophet_message}
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
