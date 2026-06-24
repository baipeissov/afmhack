import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a 0..1 confidence as a fixed 2-decimal string, e.g. 0.94 */
export function fmtConf(v: number): string {
  return v.toFixed(2);
}

/** Compact relative-age label from minutes, e.g. 42m, 3h, 2d */
export function fmtAge(minutes: number): string {
  if (minutes < 60) return `${Math.round(minutes)}m`;
  if (minutes < 60 * 24) return `${Math.round(minutes / 60)}h`;
  return `${Math.round(minutes / (60 * 24))}d`;
}

/** Truncate a long id/hash/wallet, e.g. 0x4a3f…e1 */
export function truncMiddle(s: string, head = 4, tail = 2): string {
  if (s.length <= head + tail + 1) return s;
  return `${s.slice(0, head)}…${s.slice(-tail)}`;
}
