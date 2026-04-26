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
import { Download, Trash2, Ban } from "lucide-react";
import { Paginator } from "../components/Paginator";
import { EmailStatusBadge } from "../components/EmailStatusBadge";
import type { WhitelistEntry, PaginatedState } from "@/types";

interface WhitelistTabProps {
  whitelist: PaginatedState<WhitelistEntry>;
  pageSize: number;
  onLoad: (skip: number) => void;
  onExportPage: () => void;
  onExportFull: () => void;
  onAskDelete: (entry: WhitelistEntry) => void;
  onAskBlacklist: (entry: WhitelistEntry) => void;
}

export const WhitelistTab: React.FC<WhitelistTabProps> = ({
  whitelist,
  pageSize,
  onLoad,
  onExportPage,
  onExportFull,
  onAskDelete,
  onAskBlacklist,
}) => {
  return (
    <>
      <div className="flex items-center justify-between mb-3">
        <div className="font-display font-semibold">
          Cabinet roster · <span className="tabular font-mono text-foreground/70">{whitelist.total}</span>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={!whitelist.items.length}
            onClick={onExportPage}
            className="rounded-[var(--btn-radius)]"
            data-testid="admin-export-whitelist"
          >
            <Download size={14} className="mr-1" /> Export page
          </Button>
          <Button
            variant="default"
            size="sm"
            disabled={whitelist.total === 0}
            onClick={onExportFull}
            className="rounded-[var(--btn-radius)]"
            data-testid="admin-export-whitelist-full"
          >
            <Download size={14} className="mr-1" /> Export ALL ({whitelist.total})
          </Button>
        </div>
      </div>
      <div className="rounded-xl border border-border overflow-hidden bg-card">
        <Table data-testid="admin-whitelist-table">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[70px]">#</TableHead>
              <TableHead>Email</TableHead>
              <TableHead className="w-[70px]">Lang</TableHead>
              <TableHead className="w-[120px]">Email</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-[210px] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {whitelist.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground py-8 font-mono text-xs">
                  No transmissions yet.
                </TableCell>
              </TableRow>
            )}
            {whitelist.items.map((r) => (
              <TableRow key={r.id} data-testid={`admin-whitelist-row-${r.id}`}>
                <TableCell className="tabular font-mono">{r.position}</TableCell>
                <TableCell className="font-mono text-sm break-all">{r.email}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="font-mono text-[10px] uppercase">
                    {r.lang}
                  </Badge>
                </TableCell>
                <TableCell>
                  <EmailStatusBadge sent={r.email_sent} status={r.email_status} />
                </TableCell>
                <TableCell className="tabular font-mono text-xs text-foreground/70">
                  {new Date(r.created_at).toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  <div className="inline-flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onAskDelete(r)}
                      className="h-8 rounded-md font-mono text-xs"
                      data-testid={`admin-delete-${r.id}`}
                    >
                      <Trash2 size={14} className="mr-1" /> Delete
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onAskBlacklist(r)}
                      className="h-8 rounded-md font-mono text-xs text-[--campaign-red] border-[--campaign-red] hover:bg-[--campaign-red] hover:text-white"
                      data-testid={`admin-blacklist-${r.id}`}
                    >
                      <Ban size={14} className="mr-1" /> Blacklist
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <Paginator
        skip={whitelist.skip}
        limit={pageSize}
        total={whitelist.total}
        onChange={onLoad}
        testid="admin-whitelist-paginator"
      />
    </>
  );
};
