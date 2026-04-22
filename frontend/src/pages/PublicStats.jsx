import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RTooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Radio, ShieldCheck, Users, MessageSquare, Sparkles, ExternalLink } from "lucide-react";
import ThemeToggle from "@/components/landing/ThemeToggle";
import ActivityHeatmap from "@/components/landing/ActivityHeatmap";
import { LanguageToggle } from "@/components/landing/LanguageToggle";
import { useI18n } from "@/i18n/I18nProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function formatDateShort(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-[var(--shadow-elev-1)] font-mono text-xs">
      <div className="text-foreground font-semibold">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tabular text-foreground/80">
          <span
            className="inline-block w-2 h-2 rounded-full mr-2 align-middle"
            style={{ background: p.color }}
          />
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

function Stat({ icon: Icon, label, value, accent = "#2DD4BF" }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
        <Icon size={14} style={{ color: accent }} />
        {label}
      </div>
      <div className="mt-2 tabular font-display font-semibold text-3xl md:text-4xl">
        {value}
      </div>
    </div>
  );
}

function LangBars({ title, fr, en, testid }) {
  const total = Math.max(1, (fr || 0) + (en || 0));
  const frPct = Math.round(((fr || 0) / total) * 100);
  const enPct = 100 - frPct;
  return (
    <div className="mt-4" data-testid={testid}>
      <div className="flex items-baseline justify-between gap-2 mb-1">
        <span className="font-display font-medium text-sm">{title}</span>
        <span className="tabular font-mono text-[11px] text-muted-foreground">
          FR {fr ?? 0} · EN {en ?? 0}
        </span>
      </div>
      <div className="flex h-2.5 w-full overflow-hidden rounded-full border border-border bg-background">
        <div
          className="h-full bg-[#2DD4BF] transition-all duration-500"
          style={{ width: `${frPct}%` }}
          title={`FR ${frPct}%`}
        />
        <div
          className="h-full bg-[#F59E0B] transition-all duration-500"
          style={{ width: `${enPct}%` }}
          title={`EN ${enPct}%`}
        />
      </div>
      <div className="mt-1 flex justify-between tabular font-mono text-[10px] text-muted-foreground">
        <span>FR {frPct}%</span>
        <span>EN {enPct}%</span>
      </div>
    </div>
  );
}

export default function PublicStats() {
  const { t, lang } = useI18n();
  const [data, setData] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "$DEEPOTUS · Public Stats";
  }, []);

  const fetchData = async (nextDays = days) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/public/stats?days=${nextDays}`);
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const chartData = useMemo(
    () =>
      (data?.series || []).map((p) => ({
        date: formatDateShort(p.date),
        rawDate: p.date,
        whitelist: p.whitelist,
        chat: p.chat,
        whitelist_daily: p.whitelist_daily,
        chat_daily: p.chat_daily,
      })),
    [data],
  );

  const changeDays = (d) => {
    setDays(d);
    fetchData(d);
  };

  const generatedLabel =
    lang === "fr"
      ? "Rafraîchi automatiquement · Lecture seule · Aucune donnée personnelle"
      : "Auto-refreshed · Read-only · No personal data";

  const subtitle =
    lang === "fr"
      ? "Tableau de bord public. Transparence on-chain assumée. Pas de vente de rêve."
      : "Public dashboard. On-chain transparency by default. No dream for sale.";

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
          <Link
            to="/"
            className="font-display font-semibold tracking-tight text-base md:text-lg"
            data-testid="public-stats-home-link"
          >
            $DEEPOTUS
            <span className="hidden sm:inline text-muted-foreground text-xs ml-2 font-mono uppercase tracking-widest">
              / public-stats
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <LanguageToggle />
            <ThemeToggle />
            <Button
              asChild
              variant="outline"
              size="sm"
              className="rounded-[var(--btn-radius)]"
            >
              <Link to="/">
                <ExternalLink size={14} className="mr-1" />
                {lang === "fr" ? "Retour au site" : "Back to site"}
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          <Radio size={12} className="text-[#33ff33]" />
          {lang === "fr" ? "— TRANSPARENCE PUBLIQUE" : "— PUBLIC TRANSPARENCY"}
        </div>
        <h1
          data-testid="public-stats-title"
          className="mt-2 font-display text-3xl md:text-5xl font-semibold leading-tight"
        >
          {lang === "fr" ? "Statistiques publiques" : "Public statistics"}
        </h1>
        <p className="mt-3 text-foreground/80 max-w-2xl">{subtitle}</p>

        {/* Stats cards */}
        <div
          className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4"
          data-testid="public-stats-bento"
        >
          <Stat
            icon={Users}
            label={lang === "fr" ? "Whitelist" : "Whitelist"}
            value={data?.whitelist_count ?? "—"}
            accent="#2DD4BF"
          />
          <Stat
            icon={MessageSquare}
            label={lang === "fr" ? "Transmissions" : "Transmissions"}
            value={data?.chat_messages ?? "—"}
            accent="#F59E0B"
          />
          <Stat
            icon={Sparkles}
            label={lang === "fr" ? "Prophéties" : "Prophecies"}
            value={data?.prophecies_served ?? "—"}
            accent="#E11D48"
          />
          <Stat
            icon={ShieldCheck}
            label={lang === "fr" ? "Lancement" : "Launch"}
            value={
              data?.launch_timestamp
                ? new Date(data.launch_timestamp).toLocaleDateString(
                    undefined,
                    { month: "short", day: "numeric", year: "numeric" },
                  )
                : "—"
            }
            accent="#16A34A"
          />
        </div>

        {/* Chart */}
        <div
          className="mt-8 rounded-xl border border-border bg-card p-4 md:p-6"
          data-testid="public-stats-chart-card"
        >
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                {lang === "fr" ? "ÉVOLUTION" : "EVOLUTION"}
              </div>
              <div className="font-display font-semibold text-lg">
                {lang === "fr"
                  ? "Whitelist & Transmissions · cumulé"
                  : "Whitelist & Transmissions · cumulative"}
              </div>
            </div>
            <div className="inline-flex items-center gap-1 rounded-[var(--btn-radius)] border border-border bg-background p-0.5">
              {[7, 30, 90].map((d) => {
                const active = d === days;
                return (
                  <button
                    key={d}
                    type="button"
                    onClick={() => changeDays(d)}
                    className={`px-3 py-1 rounded-[8px] font-mono text-[11px] uppercase tracking-widest transition-colors ${
                      active
                        ? "bg-foreground text-background"
                        : "text-foreground/70 hover:text-foreground"
                    }`}
                    data-testid={`public-stats-range-${d}`}
                  >
                    {d}d
                  </button>
                );
              })}
            </div>
          </div>

          <div
            className="h-[300px] w-full"
            data-testid="public-stats-chart"
          >
            {loading && !chartData.length ? (
              <div className="h-full flex items-center justify-center text-muted-foreground font-mono text-xs">
                {lang === "fr" ? "Chargement…" : "Loading…"}
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={chartData}
                  margin={{ top: 8, right: 12, left: -18, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="pgWhite" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2DD4BF" stopOpacity={0.6} />
                      <stop offset="100%" stopColor="#2DD4BF" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="pgChat" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.55} />
                      <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="date"
                    tick={{
                      fontFamily: "IBM Plex Mono",
                      fontSize: 11,
                      fill: "hsl(var(--muted-foreground))",
                    }}
                    tickLine={false}
                    axisLine={{ stroke: "hsl(var(--border))" }}
                  />
                  <YAxis
                    tick={{
                      fontFamily: "IBM Plex Mono",
                      fontSize: 11,
                      fill: "hsl(var(--muted-foreground))",
                    }}
                    tickLine={false}
                    axisLine={{ stroke: "hsl(var(--border))" }}
                    allowDecimals={false}
                  />
                  <RTooltip content={<ChartTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="whitelist"
                    name={lang === "fr" ? "Whitelist" : "Whitelist"}
                    stroke="#2DD4BF"
                    strokeWidth={2}
                    fill="url(#pgWhite)"
                  />
                  <Area
                    type="monotone"
                    dataKey="chat"
                    name={lang === "fr" ? "Transmissions" : "Transmissions"}
                    stroke="#F59E0B"
                    strokeWidth={2}
                    fill="url(#pgChat)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#2DD4BF]" />
              {lang === "fr" ? "Whitelist (cumulé)" : "Whitelist (cumulative)"}
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
              {lang === "fr"
                ? "Transmissions IA (cumulé)"
                : "AI transmissions (cumulative)"}
            </div>
          </div>
        </div>

        {/* Activity heatmap */}
        <div
          className="mt-6 rounded-xl border border-border bg-card p-4 md:p-6"
          data-testid="public-stats-heatmap-card"
        >
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                {lang === "fr" ? "ACTIVITÉ" : "ACTIVITY"}
              </div>
              <div className="font-display font-semibold text-lg">
                {lang === "fr"
                  ? "Heat-map des transmissions · jour × heure"
                  : "Transmissions heat-map · day × hour"}
              </div>
            </div>
          </div>
          <ActivityHeatmap data={data?.activity_heatmap || []} lang={lang} />
        </div>

        {/* Lang distribution + Top sessions */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Language distribution */}
          <div
            className="lg:col-span-6 rounded-xl border border-border bg-card p-5"
            data-testid="public-stats-lang-distribution"
          >
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              {lang === "fr" ? "RÉPARTITION LANGUES" : "LANGUAGE DISTRIBUTION"}
            </div>
            <div className="font-display font-semibold mt-1">
              {lang === "fr" ? "Whitelist & transmissions · FR/EN" : "Whitelist & transmissions · FR/EN"}
            </div>

            <LangBars
              title={lang === "fr" ? "Whitelist" : "Whitelist"}
              fr={data?.lang_distribution?.whitelist?.fr ?? 0}
              en={data?.lang_distribution?.whitelist?.en ?? 0}
              testid="public-stats-lang-whitelist"
            />
            <LangBars
              title={lang === "fr" ? "Transmissions" : "Transmissions"}
              fr={data?.lang_distribution?.chat?.fr ?? 0}
              en={data?.lang_distribution?.chat?.en ?? 0}
              testid="public-stats-lang-chat"
            />

            <p className="mt-3 font-mono text-[11px] text-muted-foreground">
              {lang === "fr"
                ? "Agrégation anonyme. Aucun email, aucun contenu."
                : "Anonymous aggregation. No emails, no content."}
            </p>
          </div>

          {/* Top sessions */}
          <div
            className="lg:col-span-6 rounded-xl border border-border bg-card p-5"
            data-testid="public-stats-top-sessions"
          >
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              {lang === "fr" ? "TOP SESSIONS" : "TOP SESSIONS"}
            </div>
            <div className="font-display font-semibold mt-1">
              {lang === "fr"
                ? "5 sessions les plus actives · anonymisées"
                : "Top 5 most active sessions · anonymized"}
            </div>

            <ul className="mt-4 space-y-2">
              {(data?.top_sessions || []).map((s, i) => (
                <li
                  key={s.anon_id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background px-3 py-2"
                  data-testid={`public-stats-top-session-${i}`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="tabular font-mono text-sm text-muted-foreground w-6">
                      #{i + 1}
                    </span>
                    <span className="font-mono text-sm break-all">{s.anon_id}</span>
                    <Badge variant="outline" className="font-mono text-[10px] uppercase">
                      {s.lang}
                    </Badge>
                  </div>
                  <span className="tabular font-mono text-xs text-foreground/80">
                    {s.message_count} msg
                  </span>
                </li>
              ))}
              {(!data?.top_sessions || data.top_sessions.length === 0) && (
                <li className="text-center text-muted-foreground py-4 font-mono text-xs">
                  {lang === "fr" ? "Aucune session active." : "No active sessions yet."}
                </li>
              )}
            </ul>

            <p className="mt-3 font-mono text-[11px] text-muted-foreground">
              {lang === "fr"
                ? "IDs générés par hachage sha256 du session_id — non réversibles."
                : "IDs generated via sha256 hash of session_id — non-reversible."}
            </p>
          </div>
        </div>

        {/* Trust strip */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mb-1">
              {lang === "fr" ? "Règles on-chain" : "On-chain rules"}
            </div>
            <div className="font-display font-semibold">
              {lang === "fr"
                ? "Multisig + timelock sur le trésor"
                : "Multisig + timelock on treasury"}
            </div>
            <p className="mt-2 text-sm text-foreground/70">
              {lang === "fr"
                ? "Chaque vente contrôlée du Trésor est annoncée avant exécution, en petits blocs."
                : "Every controlled treasury sale is announced in advance, in small blocks."}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mb-1">
              {lang === "fr" ? "Aucune donnée personnelle" : "Zero personal data"}
            </div>
            <div className="font-display font-semibold">
              {lang === "fr"
                ? "Pas d'emails. Pas de chat. Pas de PII."
                : "No emails. No chat. No PII."}
            </div>
            <p className="mt-2 text-sm text-foreground/70">
              {lang === "fr"
                ? "Ce dashboard ne sert QUE des compteurs et des séries temporelles agrégés."
                : "This dashboard serves ONLY aggregated counters and time series."}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mb-1">
              {lang === "fr" ? "Avertissement" : "Disclaimer"}
            </div>
            <div className="font-display font-semibold">
              {lang === "fr"
                ? "Hautement spéculatif. Satire."
                : "Highly speculative. Satire."}
            </div>
            <p className="mt-2 text-sm text-foreground/70">
              {lang === "fr"
                ? "Ni stablecoin, ni titre, ni rendement promis. Risque de perte totale."
                : "Not a stablecoin, not a security, no yield promise. Risk of total loss."}
            </p>
          </div>
        </motion.div>

        <div className="mt-10 font-mono text-[11px] text-muted-foreground text-center">
          {generatedLabel}
          {data?.generated_at && (
            <span className="ml-2 tabular">
              · {new Date(data.generated_at).toLocaleString()}
            </span>
          )}
        </div>
      </main>
    </div>
  );
}
