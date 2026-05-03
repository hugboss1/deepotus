/**
 * AutoReviewTab — Sprint 14.2 admin surface (Infiltration Automation).
 *
 * Lives under the `Infiltration Brain` panel as the 5th tab. Purpose:
 * give the operator a single screen to (a) see at-a-glance which auto
 * verifiers are live vs blocked on a paid X tier, (b) work the
 * "x_share_submissions" pending review queue produced by Level 2
 * verifications, and (c) approve KOL auto-DM drafts created by the
 * KOL listener pipeline.
 *
 * The whole UI is intentionally self-contained: it owns its own state
 * + polling + API calls, and exposes only stable `data-testid`
 * attributes so future Playwright specs can hook in without touching
 * internals.
 *
 * Backend endpoints consumed:
 *   GET  /api/admin/infiltration/auto/status
 *   GET  /api/admin/infiltration/shares?status=pending_review
 *   POST /api/admin/infiltration/shares/{id}/review
 *   GET  /api/admin/infiltration/kol-dm-drafts?status=draft_pending_approval
 *   POST /api/admin/infiltration/kol-dm-drafts/{id}/approve
 */
import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  RefreshCcw,
  Send as SendIcon,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { logger } from "@/lib/logger";

const API: string = process.env.REACT_APP_BACKEND_URL || "";

// ---------------------------------------------------------------------
// Types — match the Pydantic shapes returned by `routers/infiltration.py`
// ---------------------------------------------------------------------

interface VerifierStatus {
  enabled: boolean;
  mode: "live" | "blocked" | "manual_review" | "draft_queue" | string;
  blocker?: string | null;
  pending_review?: number;
  pending_approval?: number;
  approved_waiting_dispatch?: number;
}

interface AutoStatus {
  telegram_join: VerifierStatus;
  x_follow: VerifierStatus;
  x_share: VerifierStatus;
  kol_dm: VerifierStatus;
}

interface ShareSubmission {
  _id: string;
  email?: string | null;
  url: string;
  status: string;
  submitted_at: string;
  reviewer_jti?: string | null;
  reviewer_note?: string | null;
  reviewed_at?: string | null;
}

interface KolDmDraft {
  _id: string;
  kol_handle: string;
  kol_tweet_url: string;
  kol_tweet_excerpt: string;
  dm_body: string;
  status: string;
  created_at: string;
  approved_at?: string | null;
  approved_by_jti?: string | null;
  dispatched_at?: string | null;
  x_dm_id?: string | null;
}

interface Props {
  /** Headers carrying the admin JWT (provided by the parent). */
  headers: Record<string, string>;
}

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------

function ChipMode({ mode, blocker }: { mode: string; blocker?: string | null }) {
  // Tone the chip against the lived state so a glance maps to action.
  const map: Record<string, { bg: string; text: string; label: string }> = {
    live: {
      bg: "bg-[#18C964]/10 border-[#18C964]/40",
      text: "text-[#18C964]",
      label: "LIVE",
    },
    blocked: {
      bg: "bg-[#E11D48]/10 border-[#E11D48]/40",
      text: "text-[#E11D48]",
      label: blocker ? `BLOCKED · ${blocker}` : "BLOCKED",
    },
    manual_review: {
      bg: "bg-[#F59E0B]/10 border-[#F59E0B]/40",
      text: "text-[#F59E0B]",
      label: "MANUAL REVIEW",
    },
    draft_queue: {
      bg: "bg-[#22D3EE]/10 border-[#22D3EE]/40",
      text: "text-[#22D3EE]",
      label: "DRAFT QUEUE",
    },
  };
  const style = map[mode] || {
    bg: "bg-muted border-border",
    text: "text-muted-foreground",
    label: mode.toUpperCase(),
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest ${style.bg} ${style.text}`}
    >
      {style.label}
    </span>
  );
}

function StatusCard({
  title,
  status,
  testid,
  extra,
}: {
  title: string;
  status: VerifierStatus | undefined;
  testid: string;
  extra?: React.ReactNode;
}) {
  return (
    <div
      className="rounded-lg border border-border bg-background/40 p-3 space-y-2"
      data-testid={testid}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {title}
        </span>
        {status ? (
          <ChipMode mode={status.mode} blocker={status.blocker} />
        ) : (
          <span className="font-mono text-[10px] text-muted-foreground">—</span>
        )}
      </div>
      {extra}
    </div>
  );
}

// ---------------------------------------------------------------------
// Main tab
// ---------------------------------------------------------------------

export default function AutoReviewTab({ headers }: Props): JSX.Element {
  const [status, setStatus] = useState<AutoStatus | null>(null);
  const [shares, setShares] = useState<ShareSubmission[]>([]);
  const [drafts, setDrafts] = useState<KolDmDraft[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  // Local edits to a draft's `dm_body` (keyed by draft id). The textarea
  // works off this map so admins can fine-tune the message before
  // approving without ever blocking on a network round-trip.
  const [draftEdits, setDraftEdits] = useState<Record<string, string>>({});

  const loadAll = useCallback(async () => {
    try {
      const [statusRes, sharesRes, draftsRes] = await Promise.all([
        axios.get<AutoStatus>(`${API}/api/admin/infiltration/auto/status`, {
          headers,
        }),
        axios.get<{ items: ShareSubmission[]; count: number }>(
          `${API}/api/admin/infiltration/shares`,
          { headers, params: { status: "pending_review", limit: 50 } },
        ),
        axios.get<{ items: KolDmDraft[]; count: number }>(
          `${API}/api/admin/infiltration/kol-dm-drafts`,
          {
            headers,
            params: { status: "draft_pending_approval", limit: 50 },
          },
        ),
      ]);
      setStatus(statusRes.data);
      setShares(sharesRes.data.items || []);
      setDrafts(draftsRes.data.items || []);
    } catch (err) {
      logger.error(err);
      toast.error("Could not load Sprint 14.2 review queues");
    } finally {
      setLoading(false);
    }
  }, [headers]);

  useEffect(() => {
    loadAll();
    // 30s polling — the operator can also hit the manual refresh button.
    const id = setInterval(loadAll, 30_000);
    return () => clearInterval(id);
  }, [loadAll]);

  async function reviewShare(submissionId: string, approve: boolean) {
    setBusyId(submissionId);
    try {
      const note = approve ? null : window.prompt(
        "Reviewer note (optional, surfaces in the audit trail):",
        "",
      );
      await axios.post(
        `${API}/api/admin/infiltration/shares/${submissionId}/review`,
        { approve, reviewer_note: note || undefined },
        { headers },
      );
      toast.success(approve ? "Submission approved (L2 unlocked)" : "Submission rejected");
      await loadAll();
    } catch (err: unknown) {
      logger.error(err);
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Review failed";
      toast.error(detail);
    } finally {
      setBusyId(null);
    }
  }

  async function approveDraft(draftId: string) {
    setBusyId(draftId);
    try {
      const finalBody = (draftEdits[draftId] ?? "").trim();
      const body = finalBody.length > 0 ? finalBody : undefined;
      await axios.post(
        `${API}/api/admin/infiltration/kol-dm-drafts/${draftId}/approve`,
        { final_body: body },
        { headers },
      );
      toast.success("KOL DM draft approved (queued for dispatch)");
      // Drop the local edit so the next render shows the persisted body.
      setDraftEdits((prev) => {
        const next = { ...prev };
        delete next[draftId];
        return next;
      });
      await loadAll();
    } catch (err: unknown) {
      logger.error(err);
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Approve failed";
      toast.error(detail);
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return (
      <div
        className="font-mono text-sm text-muted-foreground py-10 text-center"
        data-testid="auto-review-loading"
      >
        <Loader2 className="inline-block animate-spin mr-2" size={14} />
        Booting Sprint 14.2 review queues…
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="infiltration-auto-review">
      {/* --- Status chips --- */}
      <section
        className="rounded-xl border border-border bg-card p-5 space-y-3"
        data-testid="auto-status-section"
      >
        <header className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <ShieldAlert size={16} className="text-[#F59E0B]" />
            <h3 className="font-display font-semibold">Auto-verifier status</h3>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-widest"
            >
              Sprint 14.2
            </Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadAll}
            className="rounded-[var(--btn-radius)]"
            data-testid="auto-status-refresh"
          >
            <RefreshCcw size={12} className="mr-1" /> Refresh
          </Button>
        </header>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Live state of each verifier. Telegram is fully automated via
          <code className="mx-1 font-mono">getChatMember</code>. X follow
          checks stay blocked until a paid X tier is acquired. L2 share
          mentions land in the manual review queue below. KOL DMs land in
          the draft queue and require explicit operator approval.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <StatusCard
            title="Telegram join"
            status={status?.telegram_join}
            testid="auto-status-telegram"
          />
          <StatusCard
            title="X follow check"
            status={status?.x_follow}
            testid="auto-status-x-follow"
          />
          <StatusCard
            title="X share / mention"
            status={status?.x_share}
            testid="auto-status-x-share"
            extra={
              status?.x_share?.pending_review !== undefined ? (
                <div className="font-mono text-[11px] text-foreground/85">
                  pending review:{" "}
                  <span className="text-[#F59E0B]">
                    {status.x_share.pending_review}
                  </span>
                </div>
              ) : null
            }
          />
          <StatusCard
            title="KOL auto-DM"
            status={status?.kol_dm}
            testid="auto-status-kol-dm"
            extra={
              <div className="font-mono text-[11px] text-foreground/85">
                draft:{" "}
                <span className="text-[#22D3EE]">
                  {status?.kol_dm?.pending_approval ?? 0}
                </span>{" "}
                · ready:{" "}
                <span className="text-[#18C964]">
                  {status?.kol_dm?.approved_waiting_dispatch ?? 0}
                </span>
              </div>
            }
          />
        </div>
      </section>

      {/* --- L2 share submissions queue --- */}
      <section
        className="rounded-xl border border-border bg-card p-5 space-y-3"
        data-testid="share-review-section"
      >
        <header className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-[#18C964]" />
            <h3 className="font-display font-semibold">
              Level 2 share submissions
            </h3>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-widest"
            >
              {shares.length} pending
            </Badge>
          </div>
        </header>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Each row is an Agent claiming an L2 unlock by sharing a $DEEPOTUS
          tweet. Click <span className="font-mono">→</span> on the URL to
          verify it manually, then approve or reject. The Agent's clearance
          row is updated server-side on approve.
        </p>
        {shares.length === 0 ? (
          <div
            className="rounded-md border border-dashed border-border bg-background/40 px-4 py-6 text-center text-xs font-mono text-muted-foreground"
            data-testid="share-review-empty"
          >
            No pending L2 submissions — the queue is clean.
          </div>
        ) : (
          <ul className="space-y-2">
            {shares.map((s) => (
              <li
                key={s._id}
                className="rounded-lg border border-border bg-background/40 p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3"
                data-testid={`share-row-${s._id}`}
              >
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-[11px] text-muted-foreground">
                    {new Date(s.submitted_at).toLocaleString()}
                  </div>
                  <div className="text-sm font-medium truncate">
                    {s.email || "anon"}
                  </div>
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-1 text-xs font-mono text-[#22D3EE] hover:text-[#22D3EE]/80 truncate"
                    data-testid={`share-link-${s._id}`}
                  >
                    <ExternalLink size={11} />
                    <span className="truncate max-w-[420px]">{s.url}</span>
                  </a>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="rounded-[var(--btn-radius)] text-[#E11D48] hover:text-[#E11D48]/90 hover:bg-[#E11D48]/5 border-[#E11D48]/40"
                    onClick={() => reviewShare(s._id, false)}
                    disabled={busyId === s._id}
                    data-testid={`share-reject-${s._id}`}
                  >
                    <XCircle size={12} className="mr-1" /> Reject
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className="rounded-[var(--btn-radius)] bg-[#18C964] hover:bg-[#18C964]/90 text-black"
                    onClick={() => reviewShare(s._id, true)}
                    disabled={busyId === s._id}
                    data-testid={`share-approve-${s._id}`}
                  >
                    <CheckCircle2 size={12} className="mr-1" /> Approve
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* --- KOL DM drafts queue --- */}
      <section
        className="rounded-xl border border-border bg-card p-5 space-y-3"
        data-testid="kol-drafts-section"
      >
        <header className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <SendIcon size={16} className="text-[#22D3EE]" />
            <h3 className="font-display font-semibold">
              KOL auto-DM drafts (pending approval)
            </h3>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-widest"
            >
              {drafts.length} draft{drafts.length === 1 ? "" : "s"}
            </Badge>
          </div>
        </header>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Drafts produced by the KOL listener when a watched handle mentions
          $DEEPOTUS. Edit the body inline before clicking Approve. Approved
          drafts move to <code className="font-mono">approved_waiting_dispatch</code>
          and dispatch automatically once X DM tier is enabled.
        </p>
        {drafts.length === 0 ? (
          <div
            className="rounded-md border border-dashed border-border bg-background/40 px-4 py-6 text-center text-xs font-mono text-muted-foreground"
            data-testid="kol-drafts-empty"
          >
            No KOL drafts awaiting approval.
          </div>
        ) : (
          <ul className="space-y-3">
            {drafts.map((d) => {
              const localBody = draftEdits[d._id];
              const currentBody = localBody ?? d.dm_body;
              const dirty =
                localBody !== undefined && localBody !== d.dm_body;
              return (
                <li
                  key={d._id}
                  className="rounded-lg border border-border bg-background/40 p-3 space-y-2"
                  data-testid={`kol-draft-row-${d._id}`}
                >
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="font-mono text-xs text-foreground/85">
                      <span className="text-[#22D3EE]">@{d.kol_handle}</span>
                      {" · "}
                      <span className="text-muted-foreground">
                        {new Date(d.created_at).toLocaleString()}
                      </span>
                    </div>
                    <a
                      href={d.kol_tweet_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-mono text-[#22D3EE] hover:text-[#22D3EE]/80"
                      data-testid={`kol-draft-tweet-${d._id}`}
                    >
                      <ExternalLink size={11} /> view tweet
                    </a>
                  </div>
                  <div className="rounded-md border border-border/60 bg-background/40 p-2 text-[12px] text-muted-foreground italic">
                    "{d.kol_tweet_excerpt}"
                  </div>
                  <Textarea
                    value={currentBody}
                    onChange={(
                      e: React.ChangeEvent<HTMLTextAreaElement>,
                    ) =>
                      setDraftEdits((prev) => ({
                        ...prev,
                        [d._id]: e.target.value,
                      }))
                    }
                    rows={3}
                    maxLength={400}
                    className="font-mono text-xs"
                    data-testid={`kol-draft-body-${d._id}`}
                  />
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="font-mono text-[10px] text-muted-foreground">
                      {currentBody.length}/400
                      {dirty ? (
                        <span className="ml-2 text-[#F59E0B]">
                          <AlertTriangle
                            size={10}
                            className="inline-block mr-1"
                          />
                          edited
                        </span>
                      ) : null}
                    </span>
                    <Button
                      type="button"
                      size="sm"
                      className="rounded-[var(--btn-radius)] bg-[#22D3EE] hover:bg-[#22D3EE]/90 text-black"
                      onClick={() => approveDraft(d._id)}
                      disabled={busyId === d._id}
                      data-testid={`kol-draft-approve-${d._id}`}
                    >
                      <SendIcon size={12} className="mr-1" />
                      Approve {dirty ? "(edited)" : ""}
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
