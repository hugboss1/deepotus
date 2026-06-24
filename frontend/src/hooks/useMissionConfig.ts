/**
 * useMissionConfig — Sprint 21 React hook that fetches & caches the
 * runtime Mission Command Center config.
 *
 * Strategy:
 *   - Singleton fetch on first mount (module-level promise cache).
 *   - Components subscribe via context updates so a `setLang` change
 *     doesn't refetch; the config is locale-independent.
 *   - 30-second background revalidation (lightweight: ~200 bytes).
 *
 * Exposes:
 *   - ``config`` — full typed config or ``null`` while loading.
 *   - ``loading`` / ``error`` — flags.
 *   - ``vars(locale)`` — helper that returns a ``{date, snapshotDate,
 *      rewardSol, winnersCount, minInvites, minHoldingUsd}`` object
 *      suitable for the i18n ``t(key, fallback, vars)`` interpolator.
 */
import { useCallback, useEffect, useState } from "react";
import {
  fetchMissionConfig,
  formatGiveawayDate,
  type MissionConfig,
} from "@/lib/missionConfig";

// Module-level cache (survives component remounts on the same page).
let cachedConfig: MissionConfig | null = null;
let inflight: Promise<MissionConfig> | null = null;
const subscribers: Set<(c: MissionConfig | null) => void> = new Set();

async function loadOnce(): Promise<MissionConfig> {
  if (cachedConfig) return cachedConfig;
  if (inflight) return inflight;
  inflight = fetchMissionConfig()
    .then((c) => {
      cachedConfig = c;
      subscribers.forEach((fn) => fn(c));
      return c;
    })
    .finally(() => {
      inflight = null;
    });
  return inflight;
}

/** Force-refresh the cached config and notify subscribers. */
export async function refreshMissionConfig(): Promise<MissionConfig | null> {
  try {
    const c = await fetchMissionConfig();
    cachedConfig = c;
    subscribers.forEach((fn) => fn(c));
    return c;
  } catch {
    return cachedConfig;
  }
}

export interface UseMissionConfigOut {
  config: MissionConfig | null;
  loading: boolean;
  error: string | null;
  /** Returns interpolation vars suitable for `t(key, fallback, vars)`. */
  vars: (locale: "fr" | "en") => Record<string, string | number>;
  /** Refresh the config (e.g. after an admin edit). */
  refresh: () => Promise<MissionConfig | null>;
}

export function useMissionConfig(): UseMissionConfigOut {
  const [config, setConfig] = useState<MissionConfig | null>(cachedConfig);
  const [loading, setLoading] = useState<boolean>(!cachedConfig);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const sub = (c: MissionConfig | null): void => {
      if (!cancelled) setConfig(c);
    };
    subscribers.add(sub);
    loadOnce()
      .then((c) => {
        if (cancelled) return;
        setConfig(c);
        setError(null);
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setError(err.message || "failed to load config");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return (): void => {
      cancelled = true;
      subscribers.delete(sub);
    };
  }, []);

  const vars = useCallback(
    (locale: "fr" | "en"): Record<string, string | number> => {
      if (!config) return {};
      return {
        date: formatGiveawayDate(config.giveaway_draw_date_iso, locale),
        snapshotDate: formatGiveawayDate(
          config.giveaway_snapshot_date_iso,
          locale
        ),
        rewardSol: config.giveaway_reward_sol,
        winnersCount: config.giveaway_winners_count,
        minInvites: config.giveaway_min_invites,
        minHoldingUsd: config.giveaway_min_holding_usd,
      };
    },
    [config]
  );

  return { config, loading, error, vars, refresh: refreshMissionConfig };
}
