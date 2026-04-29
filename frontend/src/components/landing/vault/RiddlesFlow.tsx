/**
 * RiddlesFlow — Proof of Intelligence branch of the Terminal (Sprint 14.1).
 *
 * Five riddles of the Terminal gate Clearance Level 3. The UX unfolds in
 * five internal phases:
 *   • intro     — briefing + start button
 *   • play      — sequential riddle playback (1 of 5, 2 of 5, …)
 *   • claim     — email prompt at the FIRST correct answer (choice 3b)
 *   • wallet    — Solana wallet linking straight after claim (choice 4a)
 *   • complete  — agent confirmation + exit CTA
 *
 * State is shadowed into sessionStorage (key `deepotus_riddles_session`)
 * so the visitor can close the modal and come back where they left off
 * without re-solving past riddles. Closing the tab wipes it.
 *
 * This component is rendered by `TerminalPopup` once the visitor hits
 * the "Proof of Intelligence" CTA from either the `denied` or `sealed`
 * phases. It deliberately lives next to TerminalPopup to keep the main
 * file compact and to isolate the Level-3 flow that has a completely
 * different backend and state model.
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Mail,
  ShieldCheck,
  Wallet,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useI18n } from "@/i18n/I18nProvider";
import { logger } from "@/lib/logger";

const API: string = process.env.REACT_APP_BACKEND_URL || "";
const SESSION_KEY = "deepotus_riddles_session";
const SOLANA_ADDR_RE = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;

type RiddlePhase = "intro" | "play" | "claim" | "wallet" | "complete";

interface Riddle {
  slug: string;
  order: number;
  title: string;
  question: string;
  hint: string | null;
  enabled: boolean;
}

interface AttemptResult {
  correct: boolean;
  matched_keyword: string | null;
  solved_count: number;
  attempts_left: number | null;
}

interface PersistedSession {
  email: string | null;
  solvedSlugs: string[];
  solvedAnswers: Record<string, string>;
  currentIndex: number;
  walletLinked: boolean;
  wallet: string | null;
  phaseSnapshot?: RiddlePhase;
}

interface RiddlesFlowProps {
  onExitToTerminal: () => void;
  onCloseAll: () => void;
}

function loadSession(): PersistedSession {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) throw new Error("empty");
    const parsed = JSON.parse(raw) as PersistedSession;
    if (!parsed || typeof parsed !== "object") throw new Error("bad");
    return {
      email: parsed.email || null,
      solvedSlugs: Array.isArray(parsed.solvedSlugs) ? parsed.solvedSlugs : [],
      solvedAnswers:
        parsed.solvedAnswers && typeof parsed.solvedAnswers === "object"
          ? parsed.solvedAnswers
          : {},
      currentIndex: Number.isFinite(parsed.currentIndex)
        ? Number(parsed.currentIndex)
        : 0,
      walletLinked: Boolean(parsed.walletLinked),
      wallet: parsed.wallet || null,
      phaseSnapshot: parsed.phaseSnapshot,
    };
  } catch {
    return {
      email: null,
      solvedSlugs: [],
      solvedAnswers: {},
      currentIndex: 0,
      walletLinked: false,
      wallet: null,
    };
  }
}

function persistSession(s: PersistedSession) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(s));
  } catch (err) {
    logger.warn("riddles session persist failed", err);
  }
}

export default function RiddlesFlow({
  onExitToTerminal,
  onCloseAll,
}: RiddlesFlowProps) {
  const { t, lang } = useI18n();

  // Riddles catalog (public projection — no keywords)
  const [riddles, setRiddles] = useState<Riddle[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Session state (persistent)
  const [session, setSession] = useState<PersistedSession>(() => loadSession());
  const [phase, setPhase] = useState<RiddlePhase>(
    session.phaseSnapshot || "intro",
  );

  // Ephemeral play state
  const [answer, setAnswer] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<AttemptResult | null>(null);
  const [wrongCount, setWrongCount] = useState<number>(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [rateLimited, setRateLimited] = useState<boolean>(false);

  // Claim phase state
  const [claimEmail, setClaimEmail] = useState<string>(session.email || "");

  // Wallet phase state
  const [walletInput, setWalletInput] = useState<string>(session.wallet || "");

  // Derived values
  const activeRiddles: Riddle[] = useMemo(
    () => (riddles || []).filter((r) => r.enabled),
    [riddles],
  );
  const solvedSet = useMemo(
    () => new Set(session.solvedSlugs),
    [session.solvedSlugs],
  );
  const currentRiddle: Riddle | undefined = activeRiddles[session.currentIndex];
  const totalCount = activeRiddles.length;
  const solvedCount = session.solvedSlugs.length;
  const hasReachedLevel3 = solvedCount >= 1;

  // --- Persist session every time it changes ---
  useEffect(() => {
    persistSession({ ...session, phaseSnapshot: phase });
  }, [session, phase]);

  // --- Load riddles on mount ---
  const fetchRiddles = useCallback(async () => {
    setLoadError(null);
    try {
      const res = await fetch(
        `${API}/api/infiltration/riddles?locale=${lang}`,
        { headers: { "Accept-Language": lang } },
      );
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data: { items: Riddle[] } = await res.json();
      const sorted = [...(data.items || [])].sort(
        (a, b) => (a.order || 0) - (b.order || 0),
      );
      setRiddles(sorted);
    } catch (err) {
      logger.error("riddles load failed", err);
      setLoadError(String((err as Error)?.message || err));
    }
  }, [lang]);

  useEffect(() => {
    void fetchRiddles();
  }, [fetchRiddles]);

  // --- Helpers ---
  const advanceIndex = useCallback(
    (start: number): number => {
      // Find the next unsolved enabled riddle starting at `start`.
      for (let i = start; i < activeRiddles.length; i += 1) {
        if (!solvedSet.has(activeRiddles[i].slug)) return i;
      }
      // Fallback: return the last index if everything is solved.
      return activeRiddles.length - 1;
    },
    [activeRiddles, solvedSet],
  );

  // When riddles load (or session changes from stale data), recalibrate
  // currentIndex to the first unsolved one.
  useEffect(() => {
    if (!activeRiddles.length) return;
    if (currentRiddle && !solvedSet.has(currentRiddle.slug)) return;
    const next = advanceIndex(session.currentIndex);
    if (next !== session.currentIndex) {
      setSession((s) => ({ ...s, currentIndex: next }));
    }
  }, [activeRiddles, solvedSet, currentRiddle, advanceIndex, session.currentIndex]);

  const resetEphemeral = () => {
    setAnswer("");
    setLastResult(null);
    setWrongCount(0);
    setErrorMsg(null);
    setRateLimited(false);
  };

  // --- Submit attempt ---
  const submitAttempt = useCallback(async () => {
    if (!currentRiddle) return;
    const clean = (answer || "").trim();
    if (clean.length === 0) {
      setErrorMsg(String(t("terminal.riddles.answerPlaceholder")));
      return;
    }
    setErrorMsg(null);
    setSubmitting(true);
    try {
      const res = await fetch(
        `${API}/api/infiltration/riddles/${currentRiddle.slug}/attempt`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept-Language": lang,
          },
          body: JSON.stringify({
            answer: clean,
            email: session.email || undefined,
            locale: lang,
          }),
        },
      );
      if (res.status === 429) {
        setRateLimited(true);
        setLastResult(null);
        return;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(
          data?.detail?.error || data?.detail || `HTTP ${res.status}`,
        );
      }
      const data: AttemptResult = await res.json();
      setLastResult(data);
      if (data.correct) {
        // Persist: mark the slug as solved AND keep the winning answer so
        // we can replay it during the claim phase (backend requires a
        // correct answer + email to write the clearance row). Without
        // this, navigating to `claim` and coming back would lose the
        // winning string.
        // Using functional setSession(s => ...) so the reducer reads
        // the *latest* solvedSlugs / solvedAnswers from state instead of
        // the closure — this also lets us drop both fields from the
        // useCallback deps without a stale-state risk.
        const slug = currentRiddle.slug;
        setSession((s) => ({
          ...s,
          solvedSlugs: Array.from(new Set([...s.solvedSlugs, slug])),
          solvedAnswers: {
            ...(s.solvedAnswers || {}),
            [slug]: clean,
          },
        }));
        setWrongCount(0);
      } else {
        setWrongCount((c) => c + 1);
      }
    } catch (err) {
      logger.error("riddle submit failed", err);
      setErrorMsg(String((err as Error)?.message || err));
    } finally {
      setSubmitting(false);
    }
  }, [answer, currentRiddle, lang, session.email, t]);

  // --- Claim: submit email so backend creates the clearance row ---
  const claimLevel3 = useCallback(async () => {
    const email = (claimEmail || "").trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setErrorMsg(String(t("terminal.emailInvalid")));
      return;
    }
    if (!session.solvedSlugs.length) {
      setErrorMsg(String(t("terminal.riddles.claimError")));
      return;
    }
    setErrorMsg(null);
    setSubmitting(true);
    try {
      // Replay the latest winning answer so the backend marks the clearance
      // row against this email. We stored it in `session.solvedAnswers` at
      // the moment the user got it right — it's the only way to make the
      // backend `submit_attempt` return `correct=true` AND register the
      // solve under the now-provided email (the public surface
      // deliberately has no "bind email to already-solved slug" helper).
      const latestSlug =
        session.solvedSlugs[session.solvedSlugs.length - 1];
      const cachedAnswer = (session.solvedAnswers || {})[latestSlug] || answer;
      if (!cachedAnswer) {
        throw new Error("no cached answer to replay");
      }
      const res = await fetch(
        `${API}/api/infiltration/riddles/${latestSlug}/attempt`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept-Language": lang,
          },
          body: JSON.stringify({
            answer: cachedAnswer.slice(0, 500),
            email,
            locale: lang,
          }),
        },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        // FastAPI returns { detail: [{ type, loc, msg, ... }] } for Pydantic
        // validation errors (422). Surface the human message.
        let detailMsg: string | null = null;
        if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
          detailMsg = String(data.detail[0].msg);
        } else if (typeof data?.detail === "string") {
          detailMsg = data.detail;
        } else if (data?.detail?.error) {
          detailMsg = String(data.detail.error);
        }
        throw new Error(detailMsg || `HTTP ${res.status}`);
      }
      const data: AttemptResult = await res.json();
      if (!data.correct) {
        // Backend refused the replay — should not happen since we
        // persisted the exact string that just won, but if it does we
        // fail loudly so the user can retry.
        throw new Error("replay rejected");
      }
      setSession((s) => ({ ...s, email }));
      setPhase("wallet");
    } catch (err) {
      logger.error("claim level3 failed", err);
      const msg = String((err as Error)?.message || "");
      // Give user the raw backend detail if it's informative (email
      // validation errors are the main failure mode in practice).
      if (msg && msg !== "replay rejected") {
        setErrorMsg(msg);
      } else {
        setErrorMsg(String(t("terminal.riddles.claimError")));
      }
    } finally {
      setSubmitting(false);
    }
  }, [answer, claimEmail, lang, session.solvedSlugs, session.solvedAnswers, t]);

  // --- Link wallet ---
  const linkWallet = useCallback(async () => {
    const addr = (walletInput || "").trim();
    if (!SOLANA_ADDR_RE.test(addr)) {
      setErrorMsg(String(t("terminal.riddles.walletInvalid")));
      return;
    }
    if (!session.email) {
      setErrorMsg(String(t("terminal.emailInvalid")));
      return;
    }
    setErrorMsg(null);
    setSubmitting(true);
    try {
      const res = await fetch(
        `${API}/api/infiltration/clearance/link-wallet`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept-Language": lang,
          },
          body: JSON.stringify({
            email: session.email,
            wallet_address: addr,
          }),
        },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        let detailMsg: string | null = null;
        if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
          detailMsg = String(data.detail[0].msg);
        } else if (typeof data?.detail === "string") {
          detailMsg = data.detail;
        } else if (data?.detail?.error) {
          detailMsg = String(data.detail.error);
        }
        // Map well-known backend errors to localized copy.
        if (detailMsg && detailMsg.includes("already linked")) {
          throw new Error(String(t("terminal.riddles.walletAlreadyLinked")));
        }
        if (detailMsg && detailMsg.includes("invalid Solana")) {
          throw new Error(String(t("terminal.riddles.walletInvalid")));
        }
        throw new Error(detailMsg || `HTTP ${res.status}`);
      }
      setSession((s) => ({ ...s, wallet: addr, walletLinked: true }));
      setPhase("complete");
    } catch (err) {
      logger.error("wallet link failed", err);
      const msg = String((err as Error)?.message || "");
      setErrorMsg(msg || String(t("terminal.riddles.walletError")));
    } finally {
      setSubmitting(false);
    }
  }, [walletInput, session.email, lang, t]);

  // --- Phase transitions helpers ---
  const onStart = () => {
    resetEphemeral();
    setPhase("play");
  };

  const goToNext = () => {
    if (!currentRiddle) return;
    const next = advanceIndex(session.currentIndex + 1);
    // If everything is solved OR the user wants to claim now:
    const allSolved = activeRiddles.every((r) =>
      session.solvedSlugs.includes(r.slug),
    );
    if (allSolved && !session.email) {
      setPhase("claim");
      return;
    }
    if (allSolved && session.email) {
      setPhase(session.walletLinked ? "complete" : "wallet");
      return;
    }
    setSession((s) => ({ ...s, currentIndex: next }));
    resetEphemeral();
  };

  const goToClaim = () => {
    resetEphemeral();
    setPhase("claim");
  };

  const walletSkip = () => {
    // Accept to leave the wallet unlinked for now — go straight to complete.
    setPhase("complete");
  };

  // --- Render ---
  if (loadError) {
    return (
      <div
        className="text-center py-8 text-red-400 text-sm"
        data-testid="riddles-load-error"
      >
        <AlertTriangle size={18} className="inline-block mr-2" />
        {t("terminal.riddles.loadError")}
        <div className="mt-4">
          <Button
            onClick={() => {
              setLoadError(null);
              void fetchRiddles();
            }}
            className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
          >
            {t("terminal.retry")}
          </Button>
        </div>
      </div>
    );
  }

  if (!riddles) {
    return (
      <div
        className="text-center py-10 text-[#18C964]/80 text-sm font-mono"
        data-testid="riddles-loading"
      >
        <Loader2 size={18} className="inline-block mr-2 animate-spin" />
        {t("terminal.riddles.loading")}
      </div>
    );
  }

  if (activeRiddles.length === 0) {
    return (
      <div
        className="text-center py-10 text-[#18C964]/70 text-sm font-mono"
        data-testid="riddles-empty"
      >
        {t("terminal.riddles.empty")}
      </div>
    );
  }

  // -----------------------------------------------------------------
  // INTRO
  // -----------------------------------------------------------------
  if (phase === "intro") {
    const canResume =
      session.solvedSlugs.length > 0 && session.currentIndex > 0;
    return (
      <div data-testid="riddles-phase-intro">
        <div className="text-[#F59E0B]/80 text-[11px] mb-3 inline-flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-[#F59E0B] animate-pulse" />
          &gt; {t("terminal.riddles.introBadge")}
        </div>
        <div className="text-[#18C964] text-base font-semibold mb-3">
          {t("terminal.riddles.introTitle")}
        </div>
        <div className="text-[#18C964]/85 mb-4 leading-relaxed text-[13px]">
          {t("terminal.riddles.introBody")}
        </div>
        <ul className="space-y-1 mb-5 text-[#18C964]/70 text-[12px] font-mono">
          {(t("terminal.riddles.introHints") as string[] | undefined || []).map(
            (line, i) => (
              <li key={`hint-${i}`} className="whitespace-pre-wrap">
                {line}
              </li>
            ),
          )}
        </ul>

        {/* Progress preview */}
        <div className="mb-5 rounded-md border border-[#F59E0B]/30 bg-[#F59E0B]/5 px-3 py-2 font-mono text-[11px] text-[#F59E0B]/90 inline-flex items-center gap-2">
          <ShieldCheck size={12} />
          {t("terminal.riddles.progressLabel")}:{" "}
          <span className="text-[#F59E0B]">
            {solvedCount}
          </span>{" "}
          / {totalCount}
          {canResume && (
            <span className="ml-2 text-[10px] text-[#F59E0B]/60">
              · {t("terminal.riddles.introResume")}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Button
            onClick={onStart}
            className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
            data-testid="riddles-start"
          >
            {canResume
              ? t("terminal.riddles.introResume")
              : t("terminal.riddles.introStart")}
          </Button>
          <button
            type="button"
            onClick={onExitToTerminal}
            className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs underline decoration-dashed underline-offset-2"
            data-testid="riddles-abort"
          >
            {t("terminal.riddles.introAbort")}
          </button>
        </div>
      </div>
    );
  }

  // -----------------------------------------------------------------
  // PLAY
  // -----------------------------------------------------------------
  if (phase === "play") {
    if (!currentRiddle) {
      // Nothing left — jump straight to claim or wallet / complete.
      if (!session.email) {
        setPhase("claim");
      } else if (!session.walletLinked) {
        setPhase("wallet");
      } else {
        setPhase("complete");
      }
      return null;
    }
    const solvedThis = solvedSet.has(currentRiddle.slug);
    const showHint = wrongCount >= 3 && currentRiddle.hint;

    return (
      <div data-testid="riddles-phase-play">
        {/* Header row */}
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="text-[#F59E0B]/80 text-[11px] font-mono inline-flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-[#F59E0B] animate-pulse" />
            &gt; riddle.{session.currentIndex + 1}_of_{totalCount}
          </div>
          <div className="text-[#18C964]/70 text-[10px] font-mono uppercase tracking-widest">
            {t("terminal.riddles.progressLabel")}:{" "}
            <span className="text-[#18C964]">{solvedCount}</span>/{totalCount}
          </div>
        </div>

        {/* Title + question */}
        <div className="text-[#18C964] text-sm font-semibold mb-2">
          {currentRiddle.title}
          {solvedThis && (
            <span className="ml-2 inline-block px-2 py-0.5 rounded bg-[#18C964] text-black font-mono text-[10px] uppercase tracking-widest">
              {t("terminal.riddles.currentSolvedBadge")}
            </span>
          )}
        </div>
        <div
          className="text-[#18C964]/85 leading-relaxed text-[13px] mb-4 whitespace-pre-wrap"
          data-testid="riddle-question"
        >
          {currentRiddle.question}
        </div>

        {/* Rate-limited overlay */}
        {rateLimited && (
          <div
            className="mb-4 rounded-md border border-[#FF4D4D]/60 bg-[#FF4D4D]/10 p-3 text-[#FF4D4D] text-xs font-mono"
            data-testid="riddle-ratelimited"
          >
            <AlertTriangle size={14} className="inline-block mr-1" />
            {t("terminal.riddles.rateLimited")}
          </div>
        )}

        {/* Last result feedback */}
        {lastResult && lastResult.correct && (
          <div
            className="mb-4 rounded-md border border-[#18C964]/60 bg-[#18C964]/10 p-3 text-[#18C964] text-sm font-mono"
            data-testid="riddle-correct"
          >
            <CheckCircle2 size={14} className="inline-block mr-1" />
            <strong>{t("terminal.riddles.correctTitle")}</strong>
            <div className="text-[11px] mt-1 text-[#18C964]/80">
              {String(t("terminal.riddles.correctSub")).replace(
                "__KEYWORD__",
                lastResult.matched_keyword || "—",
              )}
            </div>
          </div>
        )}
        {lastResult && !lastResult.correct && !rateLimited && (
          <div
            className="mb-4 rounded-md border border-[#F59E0B]/50 bg-[#F59E0B]/5 p-3 text-[#F59E0B] text-xs font-mono"
            data-testid="riddle-incorrect"
          >
            <AlertTriangle size={13} className="inline-block mr-1" />
            <strong>{t("terminal.riddles.incorrectTitle")}</strong>
            {lastResult.attempts_left !== null &&
              lastResult.attempts_left !== undefined && (
                <div className="text-[11px] mt-1 text-[#F59E0B]/80">
                  {String(t("terminal.riddles.incorrectAttemptsLeft")).replace(
                    "__N__",
                    String(lastResult.attempts_left),
                  )}
                </div>
              )}
          </div>
        )}

        {/* Hint after 3 wrongs */}
        {showHint && (
          <div
            className="mb-4 rounded-md border border-[#22D3EE]/40 bg-[#22D3EE]/5 p-3 text-[#22D3EE] text-xs font-mono italic"
            data-testid="riddle-hint"
          >
            <span className="not-italic">
              {t("terminal.riddles.hintLabel")}
            </span>{" "}
            {currentRiddle.hint}
          </div>
        )}

        {/* Answer input (hidden if solvedThis and result) */}
        {!solvedThis && (
          <div className="space-y-2 max-w-lg">
            <label
              htmlFor="riddle-answer"
              className="text-[11px] text-[#18C964]/70 block"
            >
              &gt; {t("terminal.riddles.answerLabel")}
            </label>
            <Textarea
              id="riddle-answer"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder={String(t("terminal.riddles.answerPlaceholder"))}
              maxLength={500}
              rows={2}
              disabled={submitting || rateLimited}
              className="bg-black border-[#18C964]/40 focus-visible:ring-[#18C964]/60 text-[#18C964] font-mono text-sm placeholder:text-[#18C964]/30"
              data-testid="riddle-answer-input"
            />
            {errorMsg && (
              <div className="text-red-400 text-xs flex items-center gap-2">
                <AlertTriangle size={12} /> {errorMsg}
              </div>
            )}
            <div className="flex items-center gap-3 pt-1 flex-wrap">
              <Button
                onClick={submitAttempt}
                disabled={submitting || rateLimited || answer.trim() === ""}
                className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
                data-testid="riddle-submit"
              >
                {submitting ? (
                  <Loader2 size={14} className="mr-1 animate-spin" />
                ) : null}
                {submitting
                  ? t("terminal.riddles.submitting")
                  : t("terminal.riddles.submit")}
              </Button>
              <button
                type="button"
                onClick={onExitToTerminal}
                className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs underline decoration-dashed underline-offset-2"
                data-testid="riddle-back-terminal"
              >
                {t("terminal.back")}
              </button>
            </div>
          </div>
        )}

        {/* After success, continue / claim buttons */}
        {lastResult?.correct && (
          <div className="mt-5 flex items-center gap-3 flex-wrap border-t border-[#18C964]/20 pt-4">
            {session.currentIndex < totalCount - 1 && (
              <Button
                onClick={goToNext}
                className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
                data-testid="riddle-next"
              >
                {t("terminal.riddles.nextRiddle")}
              </Button>
            )}
            {hasReachedLevel3 && !session.email && (
              <Button
                onClick={goToClaim}
                variant="outline"
                className="rounded-md border-[#F59E0B] text-[#F59E0B] hover:bg-[#F59E0B]/10 font-mono font-semibold"
                data-testid="riddle-claim-now"
              >
                {t("terminal.riddles.claimNow")}
              </Button>
            )}
            {hasReachedLevel3 && session.email && !session.walletLinked && (
              <Button
                onClick={() => setPhase("wallet")}
                variant="outline"
                className="rounded-md border-[#F59E0B] text-[#F59E0B] hover:bg-[#F59E0B]/10 font-mono font-semibold"
                data-testid="riddle-to-wallet"
              >
                <Wallet size={13} className="mr-1" /> {t("terminal.riddles.walletSubmit")}
              </Button>
            )}
          </div>
        )}

        {/* Skip to claim when Level-3 reached (short-circuit for impatient users) */}
        {hasReachedLevel3 && !lastResult?.correct && !session.email && (
          <div className="mt-5 border-t border-[#18C964]/20 pt-3">
            <button
              type="button"
              onClick={goToClaim}
              className="text-[#F59E0B]/80 hover:text-[#F59E0B] font-mono text-xs underline decoration-dashed underline-offset-2"
              data-testid="riddle-skip-to-claim"
            >
              {t("terminal.riddles.skipToEnd")}
            </button>
          </div>
        )}
      </div>
    );
  }

  // -----------------------------------------------------------------
  // CLAIM
  // -----------------------------------------------------------------
  if (phase === "claim") {
    return (
      <div data-testid="riddles-phase-claim">
        <div className="text-[#F59E0B]/90 text-[11px] mb-3 inline-flex items-center gap-2 font-mono">
          <CheckCircle2 size={12} /> {t("terminal.riddles.claimBadge")}
        </div>
        <div className="text-[#F59E0B] text-base font-semibold mb-2">
          {t("terminal.riddles.claimTitle")}
        </div>
        <div className="text-[#18C964]/85 leading-relaxed text-[13px] mb-4">
          {t("terminal.riddles.claimBody")}
        </div>

        <div className="space-y-2 max-w-md">
          <label
            htmlFor="claim-email"
            className="text-[11px] text-[#F59E0B]/80 block"
          >
            &gt; {t("terminal.riddles.claimEmailLabel")}
          </label>
          <Input
            id="claim-email"
            type="email"
            value={claimEmail}
            onChange={(e) => setClaimEmail(e.target.value)}
            placeholder={String(t("terminal.emailPlaceholder"))}
            disabled={submitting}
            autoComplete="email"
            autoFocus
            className="bg-black border-[#F59E0B]/40 focus-visible:ring-[#F59E0B]/60 text-[#18C964] font-mono placeholder:text-[#18C964]/30"
            data-testid="claim-email-input"
          />
          {errorMsg && (
            <div className="text-red-400 text-xs flex items-center gap-2">
              <AlertTriangle size={12} /> {errorMsg}
            </div>
          )}
          <div className="flex items-center gap-3 pt-1 flex-wrap">
            <Button
              onClick={claimLevel3}
              disabled={submitting || claimEmail.trim() === ""}
              className="rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
              data-testid="claim-submit"
            >
              {submitting ? (
                <Loader2 size={14} className="mr-1 animate-spin" />
              ) : (
                <Mail size={14} className="mr-1" />
              )}
              {submitting
                ? t("terminal.riddles.claimSubmitting")
                : t("terminal.riddles.claimSubmit")}
            </Button>
            <button
              type="button"
              onClick={() => setPhase("play")}
              className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs underline decoration-dashed underline-offset-2"
              data-testid="claim-back"
            >
              ← {t("terminal.back")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // -----------------------------------------------------------------
  // WALLET
  // -----------------------------------------------------------------
  if (phase === "wallet") {
    return (
      <div data-testid="riddles-phase-wallet">
        <div className="text-[#F59E0B]/90 text-[11px] mb-3 inline-flex items-center gap-2 font-mono">
          <Wallet size={12} /> {t("terminal.riddles.walletBadge")}
        </div>
        <div className="text-[#F59E0B] text-base font-semibold mb-2">
          {t("terminal.riddles.walletTitle")}
        </div>
        <div className="text-[#18C964]/85 leading-relaxed text-[13px] mb-4">
          {t("terminal.riddles.walletBody")}
        </div>

        <div className="space-y-2 max-w-md">
          <label
            htmlFor="wallet-addr"
            className="text-[11px] text-[#F59E0B]/80 block"
          >
            &gt; {t("terminal.riddles.walletLabel")}
          </label>
          <Input
            id="wallet-addr"
            value={walletInput}
            onChange={(e) => setWalletInput(e.target.value)}
            placeholder={String(t("terminal.riddles.walletPlaceholder"))}
            disabled={submitting}
            spellCheck={false}
            autoCapitalize="off"
            autoCorrect="off"
            className="bg-black border-[#F59E0B]/40 focus-visible:ring-[#F59E0B]/60 text-[#18C964] font-mono text-sm tracking-wider placeholder:text-[#18C964]/30"
            data-testid="wallet-input"
          />
          {errorMsg && (
            <div className="text-red-400 text-xs flex items-center gap-2">
              <AlertTriangle size={12} /> {errorMsg}
            </div>
          )}
          <div className="flex items-center gap-3 pt-1 flex-wrap">
            <Button
              onClick={linkWallet}
              disabled={submitting || walletInput.trim() === ""}
              className="rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
              data-testid="wallet-submit"
            >
              {submitting ? (
                <Loader2 size={14} className="mr-1 animate-spin" />
              ) : (
                <Wallet size={14} className="mr-1" />
              )}
              {submitting
                ? t("terminal.riddles.walletSubmitting")
                : t("terminal.riddles.walletSubmit")}
            </Button>
            <button
              type="button"
              onClick={walletSkip}
              className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs underline decoration-dashed underline-offset-2"
              data-testid="wallet-skip"
            >
              {t("terminal.riddles.walletSkip")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // -----------------------------------------------------------------
  // COMPLETE
  // -----------------------------------------------------------------
  const completeLeadKey = session.walletLinked
    ? "terminal.riddles.completeLead"
    : "terminal.riddles.completeLeadNoWallet";
  return (
    <div data-testid="riddles-phase-complete">
      <div className="text-[#18C964]/90 text-[11px] mb-3 inline-flex items-center gap-2 font-mono">
        <CheckCircle2 size={12} /> {t("terminal.riddles.completeBadge")}
      </div>
      <div className="text-[#18C964] text-base font-semibold mb-2">
        {t("terminal.riddles.completeTitle")}
      </div>
      <div className="text-[#18C964]/85 leading-relaxed text-[13px] mb-3">
        {String(t(completeLeadKey)).replace("__SOLVED__", String(solvedCount))}
      </div>
      {session.wallet && (
        <div className="text-[11px] text-[#F59E0B]/80 font-mono mb-4 break-all">
          <Wallet size={10} className="inline-block mr-1" />
          {session.wallet}
        </div>
      )}
      <div className="text-[#18C964]/70 text-xs mb-5 leading-relaxed">
        {t("terminal.riddles.completeNext")}
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        {solvedCount < totalCount && (
          <Button
            onClick={() => {
              const next = advanceIndex(0);
              setSession((s) => ({ ...s, currentIndex: next }));
              resetEphemeral();
              setPhase("play");
            }}
            variant="outline"
            className="rounded-md border-[#F59E0B] text-[#F59E0B] hover:bg-[#F59E0B]/10 font-mono font-semibold"
            data-testid="complete-continue"
          >
            <ArrowRight size={13} className="mr-1" />
            {t("terminal.riddles.completeContinue")}
          </Button>
        )}
        <Button
          onClick={onCloseAll}
          className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
          data-testid="complete-close"
        >
          {t("terminal.riddles.completeClose")}
        </Button>
      </div>
    </div>
  );
}
