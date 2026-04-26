import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download } from "lucide-react";
import { Paginator } from "../components/Paginator";
import type { ChatLogEntry, PaginatedState } from "@/types";

interface ChatLogsTabProps {
  chatLogs: PaginatedState<ChatLogEntry>;
  pageSize: number;
  onLoad: (skip: number) => void;
  onExport: () => void;
}

export const ChatLogsTab: React.FC<ChatLogsTabProps> = ({
  chatLogs,
  pageSize,
  onLoad,
  onExport,
}) => {
  return (
    <>
      <div className="flex items-center justify-between mb-3">
        <div className="font-display font-semibold">
          Transmissions log ·{" "}
          <span className="tabular font-mono text-foreground/70">{chatLogs.total}</span>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={!chatLogs.items.length}
          onClick={onExport}
          className="rounded-[var(--btn-radius)]"
          data-testid="admin-export-chat"
        >
          <Download size={14} className="mr-1" /> Export page CSV
        </Button>
      </div>
      <div
        className="rounded-xl border border-border bg-card divide-y divide-border"
        data-testid="admin-chat-list"
      >
        {chatLogs.items.length === 0 && (
          <div className="p-8 text-center text-muted-foreground font-mono text-xs">
            No transmissions yet.
          </div>
        )}
        {chatLogs.items.map((m) => (
          <div key={m.id || m._id} className="p-4">
            <div className="flex items-center justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[10px] uppercase">
                  {m.lang}
                </Badge>
                <span className="font-mono text-xs text-foreground/70 break-all">
                  session: {m.session_id}
                </span>
              </div>
              <span className="tabular font-mono text-[10px] text-muted-foreground">
                {new Date(m.created_at).toLocaleString()}
              </span>
            </div>
            <div className="font-mono text-sm break-words">
              <span className="text-[--amber]">user :~$</span>{" "}
              <span className="text-foreground">{m.user_message}</span>
            </div>
            <div className="font-mono text-sm mt-1 break-words">
              <span className="text-[--terminal-green-dim]">DEEPOTUS:~&gt;</span>{" "}
              <span className="text-foreground/90">{m.reply}</span>
            </div>
          </div>
        ))}
      </div>
      <Paginator
        skip={chatLogs.skip}
        limit={pageSize}
        total={chatLogs.total}
        onChange={onLoad}
        testid="admin-chat-paginator"
      />
    </>
  );
};
