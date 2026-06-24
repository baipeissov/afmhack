import { cn } from "@/lib/utils";

export function LivePulseDot({
  critical = false,
  className,
}: {
  critical?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-block size-2 rounded-full",
        critical ? "ss-live-dot-crit bg-sev-critical" : "ss-live-dot bg-agent-live",
        className
      )}
    />
  );
}

export function TypingDots({ className }: { className?: string }) {
  return (
    <span className={cn("ss-typing inline-flex items-center gap-0.5", className)}>
      <span className="size-1 rounded-full bg-text-muted" />
      <span className="size-1 rounded-full bg-text-muted" />
      <span className="size-1 rounded-full bg-text-muted" />
    </span>
  );
}
