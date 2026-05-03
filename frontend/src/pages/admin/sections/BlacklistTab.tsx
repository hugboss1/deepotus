import React, { useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Download, Plus, UploadCloud, Undo2, Clock } from "lucide-react";
import type {
  BlacklistEntry,
  BlacklistImportResult,
  PaginatedState,
} from "@/types";

interface BlacklistTabProps {
  blacklist: PaginatedState<BlacklistEntry>;
  blEmail: string;
  setBlEmail: (v: string) => void;
  blReason: string;
  setBlReason: (v: string) => void;
  blCooldown: string;
  setBlCooldown: (v: string) => void;
  csvText: string;
  setCsvText: (v: string) => void;
  csvCooldown: string;
  setCsvCooldown: (v: string) => void;
  importResult: BlacklistImportResult | null;
  loading: boolean;
  onAddBlacklist: (e: React.FormEvent) => void;
  onCsvFile: (file: File | undefined) => void;
  onSubmitImport: () => void;
  onAskUnblock: (entry: BlacklistEntry) => void;
  onExport: () => void;
}

export const BlacklistTab: React.FC<BlacklistTabProps> = ({
  blacklist,
  blEmail,
  setBlEmail,
  blReason,
  setBlReason,
  blCooldown,
  setBlCooldown,
  csvText,
  setCsvText,
  csvCooldown,
  setCsvCooldown,
  importResult,
  loading,
  onAddBlacklist,
  onCsvFile,
  onSubmitImport,
  onAskUnblock,
  onExport,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div className="lg:col-span-5">
        <form onSubmit={onAddBlacklist} className="rounded-xl border border-border bg-card p-5" data-testid="admin-blacklist-add-form">
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground mb-1">Add to blacklist</div>
          <div className="font-display font-semibold">Manual addition</div>
          <div className="mt-3">
            <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Email</label>
            <Input type="email" required value={blEmail} onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setBlEmail(e.target.value)} placeholder="spam@example.com" className="mt-1 font-mono" data-testid="admin-blacklist-add-email" />
          </div>
          <div className="mt-3">
            <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Reason (optional)
            </label>
            <Input type="text" value={blReason} onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setBlReason(e.target.value)} placeholder="bot, abuse, DoS…" className="mt-1 font-mono" data-testid="admin-blacklist-add-reason" />
          </div>
          <div className="mt-3">
            <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Cooldown days (optional — auto-unblock after)
            </label>
            <Input
              type="number"
              min="0"
              max="365"
              value={blCooldown}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setBlCooldown(e.target.value)}
              placeholder="0 = permanent"
              className="mt-1 font-mono tabular"
              data-testid="admin-blacklist-add-cooldown"
            />
          </div>
          <Button type="submit" className="mt-4 w-full rounded-[var(--btn-radius)]" data-testid="admin-blacklist-add-submit">
            <Plus size={14} className="mr-1" /> Blacklist this email
          </Button>
        </form>

        <div className="mt-4 rounded-xl border border-border bg-card p-5" data-testid="admin-blacklist-import">
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground mb-1">Bulk import</div>
          <div className="font-display font-semibold">CSV upload</div>
          <p className="mt-2 text-xs text-foreground/70">
            One email per line. Optional second column = reason. Max 5000 rows per import. Header row detected.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.txt,text/csv,text/plain"
              className="hidden"
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => onCsvFile(e.target.files?.[0])}
              data-testid="admin-blacklist-csv-file"
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              className="rounded-[var(--btn-radius)]"
              data-testid="admin-blacklist-csv-pick"
            >
              <UploadCloud size={14} className="mr-1" /> Pick CSV
            </Button>
            <span className="font-mono text-xs text-muted-foreground">or paste below</span>
          </div>
          <Textarea
            value={csvText}
            onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setCsvText(e.target.value)}
            placeholder={"email,reason\nbot1@spam.io,bot\nbot2@spam.io,abuse"}
            className="mt-2 font-mono text-xs min-h-[120px]"
            data-testid="admin-blacklist-csv-text"
          />
          <div className="mt-3">
            <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Cooldown days (applies to all imported — optional)
            </label>
            <Input
              type="number"
              min="0"
              max="365"
              value={csvCooldown}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setCsvCooldown(e.target.value)}
              placeholder="0 = permanent"
              className="mt-1 font-mono tabular"
              data-testid="admin-blacklist-csv-cooldown"
            />
          </div>
          <Button
            type="button"
            onClick={onSubmitImport}
            disabled={!csvText.trim() || loading}
            className="mt-3 w-full rounded-[var(--btn-radius)]"
            data-testid="admin-blacklist-csv-submit"
          >
            {loading ? "…" : "Import"}
          </Button>
          {importResult && (
            <div
              className="mt-3 rounded-md border border-border bg-background p-3 font-mono text-xs"
              data-testid="admin-blacklist-import-result"
            >
              <div className="text-foreground/80">Imported: <span className="tabular text-[--terminal-green-dim]">{importResult.imported}</span></div>
              <div className="text-foreground/80">Skipped invalid: <span className="tabular text-[--campaign-red]">{importResult.skipped_invalid}</span></div>
              <div className="text-foreground/80">Already existed: <span className="tabular text-muted-foreground">{importResult.skipped_existing}</span></div>
              <div className="text-foreground/80">Total rows: <span className="tabular">{importResult.total_rows}</span></div>
            </div>
          )}
        </div>
      </div>

      <div className="lg:col-span-7">
        <div className="flex items-center justify-between mb-3">
          <div className="font-display font-semibold">
            Blacklist roster · <span className="tabular font-mono text-foreground/70">{blacklist.total}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled={!blacklist.items.length}
            onClick={onExport}
            className="rounded-[var(--btn-radius)]"
            data-testid="admin-export-blacklist"
          >
            <Download size={14} className="mr-1" /> Export CSV
          </Button>
        </div>
        <div className="rounded-xl border border-border overflow-hidden bg-card">
          <Table data-testid="admin-blacklist-table">
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead className="w-[180px]">Cooldown</TableHead>
                <TableHead>Blacklisted</TableHead>
                <TableHead className="w-[130px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {blacklist.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8 font-mono text-xs">
                    No blacklisted emails.
                  </TableCell>
                </TableRow>
              )}
              {blacklist.items.map((r) => {
                const now = Date.now();
                const cd = r.cooldown_until ? new Date(r.cooldown_until).getTime() : null;
                const isTemp = !!cd && cd > now;
                const isExpired = !!cd && cd <= now;
                return (
                  <TableRow key={r.id} data-testid={`admin-blacklist-row-${r.id}`}>
                    <TableCell className="font-mono text-sm break-all">{r.email}</TableCell>
                    <TableCell className="font-mono text-xs text-foreground/70">{r.reason || "—"}</TableCell>
                    <TableCell className="tabular font-mono text-xs text-foreground/70">
                      {isTemp ? (
                        <span className="inline-flex items-center gap-1 text-[--amber]">
                          <Clock size={12} /> unlocks {cd ? new Date(cd).toLocaleDateString() : "—"}
                        </span>
                      ) : isExpired ? (
                        <span className="inline-flex items-center gap-1 text-[--terminal-green-dim]">
                          auto-unblock on next registration
                        </span>
                      ) : (
                        <Badge variant="outline" className="font-mono text-[10px] uppercase">permanent</Badge>
                      )}
                    </TableCell>
                    <TableCell className="tabular font-mono text-xs text-foreground/70">
                      {r.blacklisted_at ? new Date(r.blacklisted_at).toLocaleDateString() : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onAskUnblock(r)}
                        className="h-8 rounded-md font-mono text-xs"
                        data-testid={`admin-unblock-${r.id}`}
                      >
                        <Undo2 size={14} className="mr-1" /> Unblock
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
};
