import { cn } from "@/lib/utils";

export function KpiStat({
  label,
  value,
  delta,
  deltaUp,
}: {
  label: string;
  value: number | string;
  delta?: string;
  deltaUp?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-bg-surface-1 px-4 py-3">
      <div className="text-[10px] font-medium uppercase tracking-[0.08em] text-text-muted">
        {label}
      </div>
      <div className="mt-1 font-mono text-2xl font-medium tabular-nums text-text-primary">
        {value}
      </div>
      {delta && (
        <div
          className={cn(
            "mt-0.5 text-[11px] font-mono",
            deltaUp ? "text-sev-low" : "text-text-muted"
          )}
        >
          {delta}
        </div>
      )}
    </div>
  );
}
