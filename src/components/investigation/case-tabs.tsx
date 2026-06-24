"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  { seg: "", label: "Overview" },
  { seg: "agents", label: "War Room" },
  { seg: "contradictions", label: "Contradictions" },
  { seg: "graph", label: "Graph" },
  { seg: "timeline", label: "Timeline" },
  { seg: "report", label: "Report" },
];

export function CaseTabs({ caseId }: { caseId: string }) {
  const pathname = usePathname();
  const base = `/investigations/${caseId}`;
  return (
    <div className="flex items-center gap-1 border-b border-border-subtle bg-bg-surface-1 px-4">
      {TABS.map((t) => {
        const href = t.seg ? `${base}/${t.seg}` : base;
        const active = pathname === href;
        return (
          <Link
            key={t.label}
            href={href}
            className={cn(
              "relative px-3 py-2.5 text-[13px] transition-colors",
              active
                ? "text-text-primary"
                : "text-text-muted hover:text-text-secondary"
            )}
          >
            {t.label}
            {active && (
              <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand-500" />
            )}
          </Link>
        );
      })}
    </div>
  );
}
