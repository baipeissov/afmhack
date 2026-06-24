import type { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  hint,
  action,
}: {
  icon: LucideIcon;
  title: string;
  hint?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="grid h-full place-items-center p-10 text-center">
      <div className="max-w-sm">
        <Icon className="mx-auto size-10 text-border-strong" />
        <h2 className="mt-4 text-sm font-medium text-text-primary">{title}</h2>
        {hint && <p className="mt-1 text-xs text-text-muted">{hint}</p>}
        {action && <div className="mt-4">{action}</div>}
      </div>
    </div>
  );
}
