export type Severity = "critical" | "high" | "medium" | "low" | "info";

export const SEVERITY_ORDER: Severity[] = [
  "critical",
  "high",
  "medium",
  "low",
  "info",
];

/** CSS var color for a severity. */
export function sevColor(s: Severity): string {
  return `var(--sev-${s})`;
}

/** Tailwind text color class for a severity (mapped to theme tokens). */
export function sevTextClass(s: Severity): string {
  return {
    critical: "text-sev-critical",
    high: "text-sev-high",
    medium: "text-sev-medium",
    low: "text-sev-low",
    info: "text-sev-info",
  }[s];
}

export function sevLabel(s: Severity): string {
  return { critical: "CRIT", high: "HIGH", medium: "MED", low: "LOW", info: "INFO" }[s];
}

/** Map a 0..1 confidence to a severity bucket. */
export function confToSeverity(c: number): Severity {
  if (c >= 0.9) return "critical";
  if (c >= 0.8) return "high";
  if (c >= 0.65) return "medium";
  if (c >= 0.4) return "low";
  return "info";
}
