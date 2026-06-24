import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

/** Big, legible "fraud confidence" bar that climbs as evidence accumulates. */
export function VerdictMeter({ value }: { value: number }) {
  const t = useTranslations("verdictMeter");
  const pct = Math.round(value * 100);
  const confirmed = value >= 0.9;
  const color = confirmed
    ? "var(--sev-critical)"
    : value >= 0.7
      ? "var(--sev-high)"
      : "var(--sev-medium)";
  const label = confirmed
    ? t("fraudConfirmed")
    : value >= 0.7
      ? t("strongEvidence")
      : t("gatheringEvidence");

  return (
    <div className="rounded-lg border border-border-subtle bg-bg-surface-1 px-4 py-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-text-muted">
          {t("fraudConfidence")}
        </span>
        <span
          className={cn("text-xs font-semibold uppercase tracking-wide")}
          style={{ color }}
        >
          {label}
        </span>
      </div>
      <div className="mt-2 flex items-center gap-3">
        <div className="h-3 flex-1 overflow-hidden rounded-full bg-bg-surface-3">
          <div
            className="h-full rounded-full transition-[width] duration-700 ease-out"
            style={{ width: `${pct}%`, backgroundColor: color }}
          />
        </div>
        <span
          className="w-14 text-right font-mono text-2xl font-medium tabular-nums"
          style={{ color }}
        >
          {pct}%
        </span>
      </div>
    </div>
  );
}
