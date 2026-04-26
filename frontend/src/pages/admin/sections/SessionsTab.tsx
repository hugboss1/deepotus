import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ShieldCheck,
  Ban,
  KeyRound,
  MonitorSmartphone,
  RotateCw,
} from "lucide-react";
import type {
  AdminSession,
  PaginatedState,
  TwoFAStatus,
} from "@/types";

interface SessionsTabProps {
  sessions: PaginatedState<AdminSession>;
  twofaStatus: TwoFAStatus | null;
  onAskRevokeSession: (entry: AdminSession) => void;
  onAskRevokeOthers: () => void;
  onAskRotateSecret: () => void;
  onEnable2FA: () => void;
  onDisable2FA: () => void;
}

export const SessionsTab: React.FC<SessionsTabProps> = ({
  sessions,
  twofaStatus,
  onAskRevokeSession,
  onAskRevokeOthers,
  onAskRotateSecret,
  onEnable2FA,
  onDisable2FA,
}) => {
  return (
    <>
      <div
        className="rounded-xl border border-border bg-card p-5 mb-5"
        data-testid="admin-2fa-card"
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground flex items-center gap-2">
              <ShieldCheck size={12} /> TWO-FACTOR AUTHENTICATION
            </div>
            <div className="mt-1 font-display font-semibold flex items-center gap-2">
              {twofaStatus?.enabled ? (
                <>
                  <span>Enabled</span>
                  <Badge className="bg-[--terminal-green-dim] hover:bg-[--terminal-green-dim] text-white font-mono text-[10px] uppercase">active</Badge>
                </>
              ) : twofaStatus?.setup_pending ? (
                <>
                  <span>Setup pending</span>
                  <Badge variant="outline" className="font-mono text-[10px] uppercase text-[--amber] border-[--amber]">pending</Badge>
                </>
              ) : (
                <>
                  <span>Disabled</span>
                  <Badge variant="outline" className="font-mono text-[10px] uppercase">off</Badge>
                </>
              )}
            </div>
            {twofaStatus?.enabled && (
              <div className="mt-1 font-mono text-[11px] text-muted-foreground">
                Backup codes remaining: <span className="tabular text-foreground/80">{twofaStatus.backup_codes_remaining ?? 0}</span>
                {twofaStatus.enabled_at && <span> · enabled {new Date(twofaStatus.enabled_at).toLocaleDateString()}</span>}
              </div>
            )}
          </div>
          <div className="flex gap-2">
            {twofaStatus?.enabled ? (
              <Button
                variant="outline"
                onClick={onDisable2FA}
                className="rounded-[var(--btn-radius)] text-[--campaign-red] border-[--campaign-red]"
                data-testid="admin-2fa-disable-button"
              >
                Disable 2FA
              </Button>
            ) : (
              <Button
                onClick={onEnable2FA}
                className="rounded-[var(--btn-radius)]"
                data-testid="admin-2fa-enable-button"
              >
                <ShieldCheck size={14} className="mr-1" /> Enable 2FA
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        <div className="font-display font-semibold flex items-center gap-2">
          <KeyRound size={16} /> Active admin sessions ·{" "}
          <span className="tabular font-mono text-foreground/70">{sessions.total}</span>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onAskRevokeOthers}
            className="rounded-[var(--btn-radius)]"
            data-testid="admin-sessions-revoke-others"
          >
            <MonitorSmartphone size={14} className="mr-1" /> Revoke others
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onAskRotateSecret}
            className="rounded-[var(--btn-radius)] text-[--campaign-red] border-[--campaign-red] hover:bg-[--campaign-red] hover:text-white"
            data-testid="admin-sessions-rotate-secret"
          >
            <RotateCw size={14} className="mr-1" /> Rotate JWT secret
          </Button>
        </div>
      </div>
      <div className="rounded-xl border border-border overflow-hidden bg-card">
        <Table data-testid="admin-sessions-table">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[160px]">JTI</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Last seen</TableHead>
              <TableHead>IP</TableHead>
              <TableHead className="w-[150px]">Status</TableHead>
              <TableHead className="w-[140px] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sessions.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground py-8 font-mono text-xs">
                  No active sessions.
                </TableCell>
              </TableRow>
            )}
            {sessions.items.map((s) => (
              <TableRow key={s.jti} data-testid={`admin-session-row-${s.jti}`}>
                <TableCell className="font-mono text-xs break-all">{s.jti}</TableCell>
                <TableCell className="tabular font-mono text-xs text-foreground/70">{new Date(s.created_at).toLocaleString()}</TableCell>
                <TableCell className="tabular font-mono text-xs text-foreground/70">{s.last_seen_at ? new Date(s.last_seen_at).toLocaleString() : "—"}</TableCell>
                <TableCell className="font-mono text-xs">{s.ip || "—"}</TableCell>
                <TableCell>
                  {s.revoked ? (
                    <Badge variant="outline" className="font-mono text-[10px] uppercase text-[--campaign-red] border-[--campaign-red]">revoked</Badge>
                  ) : s.is_current ? (
                    <Badge className="font-mono text-[10px] uppercase bg-[--terminal-green-dim] hover:bg-[--terminal-green-dim]">current</Badge>
                  ) : (
                    <Badge variant="outline" className="font-mono text-[10px] uppercase">active</Badge>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {!s.revoked && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onAskRevokeSession(s)}
                      className="h-8 rounded-md font-mono text-xs"
                      data-testid={`admin-session-revoke-${s.jti}`}
                    >
                      <Ban size={14} className="mr-1" /> Revoke
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="mt-3 rounded-md border border-border bg-background/60 p-3 font-mono text-[11px] text-foreground/70">
        <strong className="text-foreground">Rotate JWT secret</strong> invalidates <em>all</em> sessions immediately, including the current one. Use after any suspected compromise.
      </div>
    </>
  );
};
