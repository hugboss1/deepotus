import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  ArrowLeft,
  Mail,
  RefreshCcw,
  ChevronLeft,
  ChevronRight,
  Filter,
} from "lucide-react";
import { toast } from "sonner";
import ThemeToggle from "@/components/landing/ThemeToggle";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const TOKEN_KEY = "deepotus_admin_token";
const PAGE_SIZE = 50;

const TYPE_COLOR = {
  "email.sent": "#F59E0B",
  "email.delivered": "#16A34A",
  "email.delivery_delayed": "#CA8A04",
  "email.bounced": "#E11D48",
  "email.complained": "#E11D48",
  "email.opened": "#2DD4BF",
  "email.clicked": "#2DD4BF",
};

export default function AdminEmails() {
  const navigate = useNavigate();
  const [token, setToken] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) || "" : "",
  );
  const [events, setEvents] = useState({
    items: [],
    total: 0,
    skip: 0,
    type_counts: {},
  });
  const [loading, setLoading] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");
  const [recipientFilter, setRecipientFilter] = useState("");

  useEffect(() => {
    document.title = "DEEPOTUS · Email Events";
    if (!token) {
      navigate("/admin");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const load = async (skip = 0) => {
    if (!token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(PAGE_SIZE));
      params.set("skip", String(skip));
      if (typeFilter) params.set("type", typeFilter);
      if (recipientFilter) params.set("recipient", recipientFilter.trim());
      const r = await axios.get(
        `${API}/admin/email-events?${params.toString()}`,
        { headers: authHeaders },
      );
      setEvents({
        items: r.data.items || [],
        total: r.data.total || 0,
        skip,
        type_counts: r.data.type_counts || {},
      });
    } catch (err) {
      if (err?.response?.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        setToken("");
        navigate("/admin");
      } else {
        toast.error("Failed to fetch events.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) load(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, typeFilter]);

  const applyRecipientFilter = (e) => {
    e.preventDefault();
    load(0);
  };

  const page = Math.floor(events.skip / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil((events.total || 0) / PAGE_SIZE));

  const typeChips = useMemo(() => {
    const entries = Object.entries(events.type_counts || {});
    entries.sort((a, b) => b[1] - a[1]);
    return entries;
  }, [events.type_counts]);

  if (!token) return null;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              to="/admin"
              className="inline-flex items-center gap-1 text-sm font-mono text-foreground/70 hover:text-foreground"
              data-testid="email-events-back"
            >
              <ArrowLeft size={14} /> back to cabinet
            </Link>
            <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              /emails
            </span>
            <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-widest">
              webhook feed
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => load(events.skip)}
              disabled={loading}
              className="rounded-[var(--btn-radius)]"
              data-testid="email-events-refresh"
            >
              <RefreshCcw size={14} className={`mr-1 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="email-events-page">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          <Mail size={12} /> — WEBHOOK FEED
        </div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-semibold leading-tight">
          Email Events
        </h1>
        <p className="mt-2 text-foreground/80">
          Every event Resend has transmitted to your webhook endpoint. Filter by type or recipient to drill down.
        </p>

        {/* Filters */}
        <div className="mt-6 flex flex-col gap-3">
          <div className="flex flex-wrap gap-2" data-testid="email-events-type-chips">
            <button
              onClick={() => setTypeFilter("")}
              className={`px-3 py-1 rounded-full border text-xs font-mono transition-colors ${
                !typeFilter
                  ? "bg-foreground text-background border-foreground"
                  : "border-border hover:bg-secondary"
              }`}
              data-testid="email-events-type-all"
            >
              All ({events.total})
            </button>
            {typeChips.map(([t, n]) => {
              const active = typeFilter === t;
              return (
                <button
                  key={t}
                  onClick={() => setTypeFilter(t)}
                  className={`px-3 py-1 rounded-full border text-xs font-mono transition-colors ${
                    active
                      ? "bg-foreground text-background border-foreground"
                      : "border-border hover:bg-secondary"
                  }`}
                  data-testid={`email-events-type-${t}`}
                  style={!active ? { color: TYPE_COLOR[t] } : {}}
                >
                  {t} ({n})
                </button>
              );
            })}
          </div>

          <form onSubmit={applyRecipientFilter} className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 max-w-md">
              <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Filter by recipient (exact email)"
                value={recipientFilter}
                onChange={(e) => setRecipientFilter(e.target.value)}
                className="pl-9 font-mono text-sm"
                data-testid="email-events-recipient-filter"
              />
            </div>
            <Button type="submit" variant="outline" className="rounded-[var(--btn-radius)]">
              Apply
            </Button>
            {recipientFilter && (
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setRecipientFilter("");
                  load(0);
                }}
                className="text-xs"
              >
                Clear
              </Button>
            )}
          </form>
        </div>

        {/* Table */}
        <div className="mt-6 rounded-xl border border-border overflow-hidden bg-card">
          <Table data-testid="email-events-table">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[160px]">Type</TableHead>
                <TableHead>Recipient</TableHead>
                <TableHead className="w-[220px]">Email ID</TableHead>
                <TableHead className="w-[200px]">Received</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.items.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="text-center text-muted-foreground py-10 font-mono text-xs"
                  >
                    No events yet. Configure the webhook on resend.com/webhooks to start receiving.
                  </TableCell>
                </TableRow>
              )}
              {events.items.map((e) => (
                <TableRow key={e.id} data-testid={`email-events-row-${e.id}`}>
                  <TableCell>
                    <span
                      className="font-mono text-xs px-2 py-0.5 rounded-full border border-border"
                      style={{ color: TYPE_COLOR[e.type] || "inherit" }}
                    >
                      {e.type}
                    </span>
                  </TableCell>
                  <TableCell className="font-mono text-sm break-all">{e.recipient || "—"}</TableCell>
                  <TableCell className="font-mono text-xs text-foreground/70 break-all">{e.email_id || "—"}</TableCell>
                  <TableCell className="tabular font-mono text-xs text-foreground/70">
                    {e.received_at ? new Date(e.received_at).toLocaleString() : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-3 font-mono text-xs" data-testid="email-events-paginator">
          <div className="text-muted-foreground">
            {events.total > 0
              ? `Rows ${events.skip + 1}–${Math.min(events.total, events.skip + PAGE_SIZE)} / ${events.total}`
              : "No rows"}
          </div>
          <div className="inline-flex items-center gap-1">
            <Button
              size="sm"
              variant="outline"
              disabled={events.skip <= 0}
              onClick={() => load(Math.max(0, events.skip - PAGE_SIZE))}
              className="h-8 rounded-md"
              data-testid="email-events-prev"
            >
              <ChevronLeft size={14} /> Prev
            </Button>
            <span className="px-3 tabular text-foreground/80">
              {page} / {totalPages}
            </span>
            <Button
              size="sm"
              variant="outline"
              disabled={events.skip + PAGE_SIZE >= events.total}
              onClick={() => load(Math.min((totalPages - 1) * PAGE_SIZE, events.skip + PAGE_SIZE))}
              className="h-8 rounded-md"
              data-testid="email-events-next"
            >
              Next <ChevronRight size={14} />
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
