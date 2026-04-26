/**
 * Curated "hack" terminal scripts for the DeepStateIntro.
 *
 * Migrated from .js → .ts (Sprint 5 TS migration). Behaviour unchanged.
 *
 * Each script is an array of lines that get typed out in sequence by
 * <TerminalWindow />. Lines carry a per-line color (`tone`) and an
 * optional `progress` field (used by the ΔΣ-handshake terminal so the
 * progress bar fills smoothly).
 *
 * Mix language strategy (validated by user):
 *   - shell/code lines stay in English (universal)
 *   - dramatic phrases use French ("ACCÈS AUTORISÉ", "DÉCHIFFREMENT")
 *
 * IMPORTANT — no real exploit names, no offensive content. The "CVE" code
 * below is intentionally fake (ΔΣ-CVE-2026-0001) to stay tongue-in-cheek.
 */

import type { Lang } from "@/types";

export type LineTone = "muted" | "ok" | "info" | "warn" | "danger";

export interface ScriptLine {
  text: string;
  tone: LineTone;
  /** Optional progress (0-100) when the line carries an ASCII progress bar. */
  progress?: number;
}

export const TERMINAL_1_LINES: ScriptLine[] = [
  { text: "> initializing kernel module deepstate.ko ...", tone: "muted" },
  { text: "[OK] kernel.deepstate v4.13.7 loaded", tone: "ok" },
  { text: "[OK] socket bound :1337", tone: "ok" },
  { text: "[OK] tor circuit established (3 hops)", tone: "ok" },
  { text: "> probing PROTOCOL ΔΣ ...", tone: "muted" },
  { text: "[..] waiting for ΔΣ handshake ack", tone: "muted" },
];

export const TERMINAL_2_LINES: ScriptLine[] = [
  { text: "$ nmap -sS deepstate.gov", tone: "muted" },
  { text: "Starting Nmap 7.94 ( https://nmap.org )", tone: "muted" },
  { text: "Discovered open ports : 22, 80, 443, 1337", tone: "info" },
  { text: "23 ports filtered by classified firewall", tone: "warn" },
  { text: "[*] exploiting ΔΣ-CVE-2026-0001 ...", tone: "warn" },
  { text: "[+] payload delivered · session opened", tone: "ok" },
];

export const TERMINAL_3_LINES: ScriptLine[] = [
  { text: "> DÉCHIFFREMENT HANDSHAKE ΔΣ ...", tone: "info" },
  { text: "[░░░░░░░░░░░░░░░░░░░░] 0%", tone: "muted", progress: 0 },
  { text: "[████░░░░░░░░░░░░░░░░] 21%", tone: "muted", progress: 21 },
  { text: "[█████████░░░░░░░░░░░] 47%", tone: "info", progress: 47 },
  { text: "[██████████████░░░░░░] 73%", tone: "info", progress: 73 },
  { text: "[████████████████████] 100%", tone: "ok", progress: 100 },
  { text: "> KEY: 7B91-ΔΣ04-CAFE-1337", tone: "ok" },
];

export const TERMINAL_4_LINES: ScriptLine[] = [
  { text: "> ACCÈS AUTORISÉ", tone: "danger" },
  { text: "> TARGET: $DEEPOTUS", tone: "warn" },
  { text: "> CHANNEL: PROTOCOL ΔΣ ACQUIRED", tone: "info" },
  { text: "> identity masked · agent registered", tone: "muted" },
  { text: "> WELCOME TO THE INSIDE.", tone: "danger" },
];

/** Header shown briefly before terminals open. */
export const PROLOGUE_LINE = "PROTOCOL ΔΣ · INITIATING SECURE BOOT ...";

/** Final dramatic line that flashes during the glitch phase. */
export const FINALE_LINE = "WELCOME TO THE INSIDE.";

/** Skip hint shown at the bottom-right throughout the intro. */
export const SKIP_HINT: Record<Lang, string> = {
  fr: "PASSER · ESC",
  en: "SKIP · ESC",
};
