import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { KeyRound, ShieldCheck, Eye, EyeOff } from "lucide-react";
import { logger } from "@/lib/logger";

interface PasswordStatus {
  using_db_override: boolean;
  rotated_at: string | null;
  rotation_count: number;
  twofa_enabled: boolean;
}

interface PasswordCardProps {
  api: string;
  headers: { Authorization: string };
}

interface StrengthCheck {
  ok: boolean;
  reasons: string[];
  score: number; // 0..4
}

function evaluateStrength(pw: string): StrengthCheck {
  const reasons: string[] = [];
  if (pw.length < 12) reasons.push("≥12 characters");
  if (!/[a-zA-Z]/.test(pw)) reasons.push("at least 1 letter");
  if (!/\d/.test(pw)) reasons.push("at least 1 digit");
  // eslint-disable-next-line no-useless-escape
  if (!/[^a-zA-Z0-9]/.test(pw)) reasons.push("at least 1 special char");
  let score = 0;
  if (pw.length >= 12) score += 1;
  if (pw.length >= 16) score += 1;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score += 1;
  if (/[^a-zA-Z0-9]/.test(pw)) score += 1;
  return { ok: reasons.length === 0, reasons, score };
}

export const PasswordCard: React.FC<PasswordCardProps> = ({ api, headers }) => {
  const [status, setStatus] = useState<PasswordStatus | null>(null);
  const [busy, setBusy] = useState<boolean>(false);

  const [currentPw, setCurrentPw] = useState<string>("");
  const [newPw, setNewPw] = useState<string>("");
  const [confirmPw, setConfirmPw] = useState<string>("");
  const [totpCode, setTotpCode] = useState<string>("");
  const [revealCurrent, setRevealCurrent] = useState<boolean>(false);
  const [revealNew, setRevealNew] = useState<boolean>(false);

  const loadStatus = async () => {
    try {
      const { data } = await axios.get<PasswordStatus>(
        `${api}/api/admin/password/status`,
        { headers },
      );
      setStatus(data);
    } catch (e) {
      logger.error(e);
    }
  };

  useEffect(() => {
    loadStatus();
    // Reload also when the parent passes a fresh `headers` (token rotated etc.)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, headers]);

  const strength = evaluateStrength(newPw);
  const matches = newPw && newPw === confirmPw;
  const canSubmit =
    !busy &&
    currentPw.length > 0 &&
    strength.ok &&
    matches &&
    (!status?.twofa_enabled || totpCode.trim().length === 6);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    try {
      const body: {
        current_password: string;
        new_password: string;
        totp_code?: string;
      } = {
        current_password: currentPw,
        new_password: newPw,
      };
      if (status?.twofa_enabled) body.totp_code = totpCode.trim();
      await axios.post(`${api}/api/admin/password/change`, body, { headers });
      toast.success(
        "Password rotated. Existing sessions stay valid — re-login may be required on other devices.",
      );
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
      setTotpCode("");
      await loadStatus();
    } catch (err: unknown) {
      // eslint-disable-next-line
      const detail = (err as any)?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Password change failed");
      logger.error(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="rounded-xl border border-border bg-card p-5 mb-5"
      data-testid="admin-password-card"
    >
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground flex items-center gap-2">
            <KeyRound size={12} /> ADMIN PASSWORD
          </div>
          <div className="mt-1 font-display font-semibold flex items-center gap-2">
            <span>Rotate cabinet password</span>
            {status?.using_db_override ? (
              <Badge
                variant="outline"
                className="font-mono text-[10px] uppercase border-[#18C964]/50 text-[#18C964]"
              >
                DB override · rotated {status.rotation_count}×
              </Badge>
            ) : (
              <Badge
                variant="outline"
                className="font-mono text-[10px] uppercase"
              >
                bootstrap (env)
              </Badge>
            )}
            {status?.twofa_enabled && (
              <Badge
                variant="outline"
                className="font-mono text-[10px] uppercase border-[#F59E0B]/50 text-[#F59E0B]"
              >
                <ShieldCheck size={10} className="mr-1" /> 2FA enforced
              </Badge>
            )}
          </div>
          {status?.rotated_at && (
            <div className="mt-1 font-mono text-[11px] text-muted-foreground">
              last rotation:{" "}
              <span className="text-foreground/80">
                {new Date(status.rotated_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      <form
        onSubmit={submit}
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
        data-testid="admin-password-form"
      >
        {/* Current password */}
        <div className="md:col-span-2">
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            Current password
          </Label>
          <div className="relative mt-1">
            <Input
              type={revealCurrent ? "text" : "password"}
              value={currentPw}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setCurrentPw(e.target.value)}
              autoComplete="current-password"
              className="font-mono pr-10"
              data-testid="admin-password-current"
              disabled={busy}
            />
            <button
              type="button"
              onClick={() => setRevealCurrent((v) => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={revealCurrent ? "Hide password" : "Show password"}
              data-testid="admin-password-current-reveal"
            >
              {revealCurrent ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>

        {/* New password */}
        <div>
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            New password
          </Label>
          <div className="relative mt-1">
            <Input
              type={revealNew ? "text" : "password"}
              value={newPw}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setNewPw(e.target.value)}
              autoComplete="new-password"
              className="font-mono pr-10"
              data-testid="admin-password-new"
              disabled={busy}
            />
            <button
              type="button"
              onClick={() => setRevealNew((v) => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={revealNew ? "Hide password" : "Show password"}
              data-testid="admin-password-new-reveal"
            >
              {revealNew ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
          {/* Strength meter */}
          {newPw && (
            <div className="mt-2" data-testid="admin-password-strength">
              <div className="flex gap-1">
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className={`h-1 flex-1 rounded-full transition-colors ${
                      i < strength.score
                        ? strength.score >= 4
                          ? "bg-[#18C964]"
                          : strength.score >= 3
                          ? "bg-[#F59E0B]"
                          : "bg-[#FF4D4D]"
                        : "bg-border"
                    }`}
                  />
                ))}
              </div>
              {!strength.ok && (
                <div className="mt-1 font-mono text-[10px] text-[#FF4D4D]">
                  Need: {strength.reasons.join(" · ")}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Confirm */}
        <div>
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            Confirm new password
          </Label>
          <Input
            type={revealNew ? "text" : "password"}
            value={confirmPw}
            onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setConfirmPw(e.target.value)}
            autoComplete="new-password"
            className="mt-1 font-mono"
            data-testid="admin-password-confirm"
            disabled={busy}
          />
          {confirmPw && !matches && (
            <div className="mt-1 font-mono text-[10px] text-[#FF4D4D]">
              Mismatch — retype.
            </div>
          )}
        </div>

        {/* 2FA code (only if 2FA is enabled) */}
        {status?.twofa_enabled && (
          <div className="md:col-span-2 animate-in fade-in-0 slide-in-from-top-2 duration-200">
            <Label className="text-xs text-muted-foreground uppercase tracking-widest">
              2FA code (or backup code)
            </Label>
            <Input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={totpCode}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
                setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 8))
              }
              placeholder="000000"
              className="mt-1 font-mono tabular text-lg text-center max-w-[180px]"
              data-testid="admin-password-totp"
              disabled={busy}
            />
          </div>
        )}

        <div className="md:col-span-2 flex items-center justify-between pt-1">
          <div className="font-mono text-[11px] text-muted-foreground">
            Existing sessions stay valid. Other devices may need to re-login.
          </div>
          <Button
            type="submit"
            disabled={!canSubmit}
            className="rounded-[var(--btn-radius)] btn-press"
            data-testid="admin-password-submit"
          >
            {busy ? "…" : "Rotate password"}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default PasswordCard;
