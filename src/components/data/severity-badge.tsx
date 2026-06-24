import { cn } from "@/lib/utils";
import { sevLabel, type Severity } from "@/lib/severity";

const dotColor: Record<Severity, string> = {
  critical: "bg-sev-critical",
  high: "bg-sev-high",
  medium: "bg-sev-medium",
  low: "bg-sev-low",
  info: "bg-sev-info",
};
const textColor: Record<Severity, string> = {
  critical: "text-sev-critical",
  high: "text-sev-high",
  medium: "text-sev-medium",
  low: "text-sev-low",
  info: "text-sev-info",
};

export function SeverityBadge({
  severity,
  label,
  className,
}: {
  severity: Severity;
  label?: string;
  className?: string;
}) {
  const filled = severity === "critical" || severity === "high";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide",
        textColor[severity],
        className
      )}
    >
      <span
        className={cn(
          "size-2 rounded-full",
          dotColor[severity],
          filled ? "" : "ring-1 ring-inset ring-current bg-transparent"
        )}
      />
      {label ?? sevLabel(severity)}
    </span>
  );
}
