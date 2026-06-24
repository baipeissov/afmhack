import type { SchemeType } from "@/types/investigation";
import type { Severity } from "@/lib/severity";

export const kpis = [
  { label: "Active cases", value: 23, delta: "▲ 3 this week", deltaUp: true },
  { label: "Agents working now", value: 14, delta: "9 in conversation", deltaUp: true },
  { label: "Suspicious videos (24h)", value: 312, delta: "▲ 18%", deltaUp: true },
  { label: "Lies caught", value: 47, delta: "across all cases", deltaUp: true },
];

/** Risk inflow over 24 buckets (last 72h) — stacked by severity. */
export const riskInflow = Array.from({ length: 24 }, (_, i) => {
  const wave = Math.sin(i / 3) * 0.5 + 0.5;
  return {
    t: i,
    critical: Math.round(wave * 8 + (i > 16 ? i - 14 : 0)),
    high: Math.round(wave * 14 + 4),
    medium: Math.round(wave * 20 + 8),
  };
});

export const schemeMix: { scheme: SchemeType; label: string; pct: number }[] = [
  { scheme: "pyramid", label: "Pyramid", pct: 48 },
  { scheme: "casino", label: "Illegal casino", pct: 31 },
  { scheme: "phishing", label: "Phishing", pct: 14 },
  { scheme: "scam", label: "Other scam", pct: 7 },
];

export interface LiveAgent {
  id: string;
  case: string;
  state: "typing" | "reply" | "idle";
}
export const liveAgents: LiveAgent[] = [
  { id: "a_03", case: "CASE-2041", state: "typing" },
  { id: "a_07", case: "CASE-2041", state: "reply" },
  { id: "a_11", case: "CASE-2041", state: "typing" },
  { id: "a_19", case: "CASE-2039", state: "idle" },
];

export interface AlertItem {
  id: string;
  kind: "contradiction" | "wallet" | "report";
  text: string;
  severity: Severity;
}
export const alerts: AlertItem[] = [
  { id: "al1", kind: "contradiction", text: "Contradiction: a_03 ✕ a_11 (regulation)", severity: "critical" },
  { id: "al2", kind: "wallet", text: "Wallet 0x4a3f…e1 linked to known cluster", severity: "high" },
  { id: "al3", kind: "report", text: "CASE-2039 report ready", severity: "info" },
];
