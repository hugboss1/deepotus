import React from "react";
import { CheckCircle2, AlertCircle, Mail } from "lucide-react";

interface EmailStatusBadgeProps {
  sent: boolean;
  status: string | null | undefined;
}

export const EmailStatusBadge: React.FC<EmailStatusBadgeProps> = ({ sent, status }) => {
  if (status === "bounced" || status === "complained") {
    return (
      <span className="inline-flex items-center gap-1 text-[--campaign-red] font-mono text-xs">
        <AlertCircle size={12} /> {status}
      </span>
    );
  }
  if (status === "delivered" || status === "opened" || status === "clicked") {
    return (
      <span className="inline-flex items-center gap-1 text-[--terminal-green-dim] font-mono text-xs">
        <CheckCircle2 size={12} /> {status}
      </span>
    );
  }
  if (sent || status === "sent") {
    return (
      <span className="inline-flex items-center gap-1 text-[--amber] font-mono text-xs">
        <Mail size={12} /> sent
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-muted-foreground font-mono text-xs">
      <AlertCircle size={12} /> pending
    </span>
  );
};
