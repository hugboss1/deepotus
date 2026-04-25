import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * `cn(...inputs)` — conditional className helper.
 *
 * Combines `clsx` (for conditional class joining) with `tailwind-merge`
 * (for de-duplicating conflicting Tailwind utilities).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
