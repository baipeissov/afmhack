"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { usePathname } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  { seg: "", key: "overview" },
  { seg: "agents", key: "warRoom" },
  { seg: "contradictions", key: "contradictions" },
  { seg: "graph", key: "graph" },
  { seg: "timeline", key: "timeline" },
  { seg: "report", key: "report" },
] as const;

export function CaseTabs({ caseId }: { caseId: string }) {
  const t = useTranslations("caseTabs");
  const pathname = usePathname();
  const base = `/investigations/${caseId}`;
  return (
    <div className="flex items-center gap-1 border-b border-border-subtle bg-bg-surface-1 px-4">
      {TABS.map((tab) => {
        const href = tab.seg ? `${base}/${tab.seg}` : base;
        const active = pathname === href;
        return (
          <Link
            key={tab.key}
            href={href}
            className={cn(
              "relative px-3 py-2.5 text-[13px] transition-colors",
              active
                ? "text-text-primary"
                : "text-text-muted hover:text-text-secondary"
            )}
          >
            {t(tab.key)}
            {active && (
              <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand-500" />
            )}
          </Link>
        );
      })}
    </div>
  );
}
