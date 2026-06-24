import { cn } from "@/lib/utils";
import { confToSeverity, sevColor } from "@/lib/severity";
import { fmtConf } from "@/lib/utils";

export function ConfidenceMeter({
  value,
  showTrend = true,
  className,
}: {
  value: number;
  showTrend?: boolean;
  className?: string;
}) {
  const color = sevColor(confToSeverity(value));
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-bg-surface-3">
        <div
          className="h-full rounded-full transition-[width] duration-500"
          style={{ width: `${value * 100}%`, backgroundColor: color }}
        />
      </div>
      <span className="font-mono text-xs tabular-nums" style={{ color }}>
        {fmtConf(value)}
      </span>
      {showTrend && <span className="text-[10px]" style={{ color }}>▲</span>}
    </div>
  );
}
