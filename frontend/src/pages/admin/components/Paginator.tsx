import React from "react";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginatorProps {
  skip: number;
  limit: number;
  total: number;
  onChange: (skip: number) => void;
  testid: string;
}

export const Paginator: React.FC<PaginatorProps> = ({ skip, limit, total, onChange, testid }) => {
  const page = Math.floor(skip / limit) + 1;
  const totalPages = Math.max(1, Math.ceil((total || 0) / limit));
  const prev = () => onChange(Math.max(0, skip - limit));
  const next = () => onChange(Math.min((totalPages - 1) * limit, skip + limit));
  return (
    <div
      className="flex items-center justify-between gap-3 mt-3 font-mono text-xs"
      data-testid={testid}
    >
      <div className="text-muted-foreground">
        {total > 0
          ? `Rows ${skip + 1}–${Math.min(total, skip + limit)} / ${total}`
          : "No rows"}
      </div>
      <div className="inline-flex items-center gap-1">
        <Button
          size="sm"
          variant="outline"
          disabled={skip <= 0}
          onClick={prev}
          className="h-8 rounded-md"
          data-testid={`${testid}-prev`}
        >
          <ChevronLeft size={14} />
          Prev
        </Button>
        <span className="px-3 tabular text-foreground/80">
          {page} / {totalPages}
        </span>
        <Button
          size="sm"
          variant="outline"
          disabled={skip + limit >= total}
          onClick={next}
          className="h-8 rounded-md"
          data-testid={`${testid}-next`}
        >
          Next
          <ChevronRight size={14} />
        </Button>
      </div>
    </div>
  );
};
