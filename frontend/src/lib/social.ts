/**
 * social.ts — Single source of truth for the $DEEPOTUS social channels.
 *
 * X and Telegram are live today (hard defaults). Instagram, Discord and
 * YouTube are "future accounts": their card/icon renders in a muted
 * "coming soon" state until the matching Vercel env var is filled, at
 * which point the channel becomes a real outbound link — same build-time
 * env pattern as the mint (see lib/launchPhase.ts). No code change /
 * redeploy of source needed to switch a channel on, just the env var.
 *
 *   REACT_APP_X_URL          (default https://x.com/deepotus_ai)
 *   REACT_APP_TELEGRAM_URL   (default https://t.me/deepotus)
 *   REACT_APP_INSTAGRAM_URL  (empty → "soon")
 *   REACT_APP_DISCORD_URL    (empty → "soon")
 *   REACT_APP_YOUTUBE_URL    (empty → "soon")
 */
import type { ComponentType } from "react";
import {
  XIcon,
  TelegramIcon,
  InstagramIcon,
  DiscordIcon,
  YoutubeIcon,
} from "@/components/landing/brandIcons";
import type { BrandIconProps } from "@/components/landing/brandIcons";

const env = (k: string): string => {
  const v = process.env[k];
  return typeof v === "string" ? v.trim() : "";
};

export type SocialKey = "x" | "telegram" | "instagram" | "discord" | "youtube";

export interface SocialChannel {
  key: SocialKey;
  Icon: ComponentType<BrandIconProps>;
  /** Brand accent. `null` → use the surrounding foreground colour
   *  (X is monochrome and must adapt to light/dark themes). */
  color: string | null;
  /** Resolved outbound URL, or "" when the account isn't live yet. */
  url: string;
  /** True once a real URL is configured (env or hard default). */
  live: boolean;
}

function make(
  key: SocialKey,
  Icon: ComponentType<BrandIconProps>,
  color: string | null,
  url: string,
): SocialChannel {
  return { key, Icon, color, url, live: Boolean(url) };
}

export const SOCIALS: SocialChannel[] = [
  make("x", XIcon, null, env("REACT_APP_X_URL") || "https://x.com/deepotus_ai"),
  make(
    "telegram",
    TelegramIcon,
    "#2AABEE",
    env("REACT_APP_TELEGRAM_URL") || "https://t.me/deepotus",
  ),
  make("instagram", InstagramIcon, "#E1306C", env("REACT_APP_INSTAGRAM_URL")),
  make("discord", DiscordIcon, "#5865F2", env("REACT_APP_DISCORD_URL")),
  make("youtube", YoutubeIcon, "#FF0000", env("REACT_APP_YOUTUBE_URL")),
];
