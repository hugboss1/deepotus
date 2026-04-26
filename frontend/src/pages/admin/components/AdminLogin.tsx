import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ShieldAlert } from "lucide-react";
import ThemeToggle from "@/components/landing/ThemeToggle";

interface AdminLoginProps {
  pwd: string;
  setPwd: (v: string) => void;
  totpCode: string;
  setTotpCode: (v: string) => void;
  twofaRequired: boolean;
  rateLimitError: string | null;
  loading: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

export const AdminLogin: React.FC<AdminLoginProps> = ({
  pwd,
  setPwd,
  totpCode,
  setTotpCode,
  twofaRequired,
  rateLimitError,
  loading,
  onSubmit,
}) => {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground p-6">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-md bg-card border border-border rounded-xl p-6 md:p-8 shadow-[var(--shadow-elev-2)]"
      >
        <div className="flex items-center gap-2 mb-1">
          <ShieldAlert size={18} className="text-[--campaign-red]" />
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
            — Cabinet Securé
          </div>
        </div>
        <h1 className="mt-2 font-display text-2xl md:text-3xl font-semibold">DEEPOTUS Admin Access</h1>
        <p className="mt-2 text-sm text-foreground/70">
          Entrez le mot de passe du cabinet pour consulter la whitelist et les logs de transmission.
        </p>
        <div className="mt-5">
          <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Password
          </label>
          <Input
            data-testid="admin-password-input"
            type="password"
            value={pwd}
            onChange={(e) => setPwd(e.target.value)}
            placeholder="••••••••"
            className="mt-1 font-mono"
            autoFocus
          />
        </div>
        {rateLimitError && (
          <div
            data-testid="admin-rate-limit-message"
            className="mt-3 rounded-md border border-[--campaign-red] bg-[--campaign-red]/10 px-3 py-2 font-mono text-xs text-[--campaign-red]"
          >
            {rateLimitError}
          </div>
        )}
        {twofaRequired && (
          <div
            data-testid="admin-2fa-code-wrapper"
            className="mt-4 animate-in fade-in-0 slide-in-from-top-2 duration-200"
          >
            <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              2FA code
            </label>
            <Input
              data-testid="admin-2fa-code-input"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="000000"
              className="mt-1 font-mono tabular text-lg text-center"
              autoFocus
            />
            <div className="mt-1 font-mono text-[10px] text-muted-foreground">
              Enter the 6-digit code from your authenticator app.
            </div>
          </div>
        )}
        <Button
          type="submit"
          disabled={loading || !pwd.trim()}
          className="mt-5 w-full rounded-[var(--btn-radius)] btn-press"
          data-testid="admin-login-button"
        >
          {loading ? "…" : "Enter the Cabinet"}
        </Button>
        <div className="mt-5 flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => navigate("/")}
            className="text-xs font-mono text-muted-foreground hover:text-foreground transition-colors"
            data-testid="admin-back-to-site"
          >
            ← back to site
          </button>
          <ThemeToggle />
        </div>
      </form>
    </div>
  );
};
