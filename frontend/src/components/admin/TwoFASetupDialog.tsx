import React, { useState } from "react";
import axios from "axios";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ShieldCheck, AlertTriangle, Copy, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Full 2FA setup flow in one dialog:
 *   step 1: show QR + secret + backup codes (generated via /2fa/setup)
 *   step 2: ask user to enter TOTP code -> POST /2fa/verify -> success
 */
export default function TwoFASetupDialog({ open, onOpenChange, token, onCompleted }) {
  const [step, setStep] = useState("start"); // start | scan | verify | done
  const [loading, setLoading] = useState(false);
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState("");
  const [copied, setCopied] = useState(false);

  const H = { Authorization: `Bearer ${token}` };

  const reset = () => {
    setStep("start");
    setSetup(null);
    setCode("");
    setCopied(false);
  };

  const startSetup = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${API}/admin/2fa/setup`, {}, { headers: H });
      setSetup(r.data);
      setStep("scan");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to start 2FA setup.");
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async () => {
    if (!code.trim()) return;
    setLoading(true);
    try {
      await axios.post(`${API}/admin/2fa/verify`, { code: code.trim() }, { headers: H });
      setStep("done");
      toast.success("2FA enabled. Keep your backup codes safe.");
      onCompleted?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Invalid code.");
    } finally {
      setLoading(false);
    }
  };

  const copyCodes = () => {
    if (!setup?.backup_codes) return;
    const txt = setup.backup_codes.join("\n");
    navigator.clipboard.writeText(txt);
    setCopied(true);
    toast.success("Backup codes copied.");
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadCodes = () => {
    if (!setup?.backup_codes) return;
    const txt = `DEEPOTUS 2FA Backup Codes
Generated: ${new Date().toISOString()}
Keep these codes offline. Each code can be used ONCE.

${setup.backup_codes.join("\n")}
`;
    const blob = new Blob([txt], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "deepotus_2fa_backup_codes.txt";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const close = (v) => {
    if (!v) reset();
    onOpenChange?.(v);
  };

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent
        data-testid="twofa-setup-dialog"
        className="max-w-lg"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-[--terminal-green-dim]" />
            Enable Two-Factor Authentication
          </DialogTitle>
          <DialogDescription>
            Add a second authentication factor to the admin login. Use any TOTP app (Google Authenticator, 1Password, Raivo, Authy, etc.).
          </DialogDescription>
        </DialogHeader>

        {step === "start" && (
          <div className="space-y-4">
            <div className="rounded-md border border-border bg-background/60 p-3 font-mono text-xs text-foreground/80 leading-relaxed">
              <div className="flex items-start gap-2">
                <AlertTriangle size={14} className="flex-none text-[--amber] mt-0.5" />
                <div>
                  Once enabled, every admin login will require your TOTP code in addition to the password.
                  You'll receive 10 backup codes — store them offline.
                </div>
              </div>
            </div>
            <Button
              onClick={startSetup}
              disabled={loading}
              className="w-full rounded-[var(--btn-radius)]"
              data-testid="twofa-start-button"
            >
              {loading ? "…" : "Generate my 2FA secret"}
            </Button>
          </div>
        )}

        {step === "scan" && setup && (
          <div className="space-y-4">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                1. Scan this QR code with your authenticator app
              </div>
              <div className="rounded-xl border border-border bg-white p-3 inline-block">
                <img
                  src={`data:image/png;base64,${setup.qr_png_base64}`}
                  alt="2FA QR code"
                  className="w-48 h-48"
                  data-testid="twofa-qr-code"
                />
              </div>
              <div className="mt-2 font-mono text-[11px] text-muted-foreground break-all">
                Manual key: <span className="text-foreground tabular">{setup.secret}</span>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  2. Save your backup codes (shown only once)
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="outline" onClick={copyCodes} className="h-7 text-xs">
                    {copied ? <CheckCircle2 size={12} className="mr-1" /> : <Copy size={12} className="mr-1" />}
                    {copied ? "Copied" : "Copy"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={downloadCodes} className="h-7 text-xs">
                    Download .txt
                  </Button>
                </div>
              </div>
              <div
                className="rounded-md border border-border bg-background/60 p-3 font-mono text-sm grid grid-cols-2 gap-x-4 gap-y-1"
                data-testid="twofa-backup-codes"
              >
                {setup.backup_codes.map((c) => (
                  <span key={c} className="tabular">{c}</span>
                ))}
              </div>
            </div>

            <div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                3. Enter the 6-digit code from your app to confirm
              </div>
              <Input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="000000"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                className="font-mono text-xl tabular text-center"
                data-testid="twofa-verify-input"
              />
              <Button
                onClick={verifyCode}
                disabled={loading || code.length !== 6}
                className="mt-3 w-full rounded-[var(--btn-radius)]"
                data-testid="twofa-verify-button"
              >
                {loading ? "…" : "Verify & Enable 2FA"}
              </Button>
            </div>
          </div>
        )}

        {step === "done" && (
          <div className="space-y-4 text-center py-4">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[--terminal-green-dim]/15 text-[--terminal-green-dim]">
              <ShieldCheck size={28} />
            </div>
            <div className="font-display font-semibold text-lg">2FA is now ACTIVE.</div>
            <p className="text-sm text-foreground/70">
              Your next login will require your password <em>and</em> a 6-digit code. Keep your backup codes in a safe place.
            </p>
            <Button onClick={() => close(false)} className="rounded-[var(--btn-radius)]" data-testid="twofa-close-done">
              Done
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
