import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { ChevronLeft, FileDown, MoreHorizontal } from "lucide-react";
import { SeverityBadge } from "@/components/data/severity-badge";
import { LivePulseDot } from "@/components/feedback/live-pulse-dot";
import { fmtConf } from "@/lib/utils";
import type { Investigation } from "@/types/investigation";

export function CaseHeader({ inv }: { inv: Investigation }) {
  const t = useTranslations("caseHeader");
  const live = inv.agentsDone < inv.agentsTotal;
  return (
    <div className="flex items-center gap-4 border-b border-border-subtle bg-bg-surface-1 px-4 py-3">
      <Link
        href="/investigations"
        className="text-text-muted transition-colors hover:text-text-primary"
      >
        <ChevronLeft className="size-4" />
      </Link>
      <div className="min-w-0">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm text-text-muted">{inv.id}</span>
          <span className="font-semibold text-text-primary">{inv.target}</span>
          <SeverityBadge severity={inv.severity} label={t("critical")} />
          <span className="text-xs uppercase tracking-wide text-text-muted">
            {inv.scheme}
          </span>
          <span className="font-mono text-sm tabular-nums text-sev-critical">
            {fmtConf(inv.confidence)}
          </span>
          {live && (
            <span className="flex items-center gap-1.5 text-xs text-agent-live">
              <LivePulseDot /> {t("live")}
            </span>
          )}
        </div>
        <p className="mt-0.5 truncate text-xs text-text-muted">
          {t("objective")}: {inv.objective}
        </p>
      </div>
      <div className="ml-auto flex items-center gap-3">
        <span className="font-mono text-sm tabular-nums text-text-secondary">
          ⏱ {inv.elapsed}
        </span>
        <Link
          href={`/investigations/${inv.id}/report`}
          className="flex items-center gap-1.5 rounded-md bg-brand-500 px-3 py-1.5 text-xs font-semibold text-bg-base transition-colors hover:bg-brand-400"
        >
          <FileDown className="size-3.5" /> {t("report")}
        </Link>
        <button className="text-text-muted hover:text-text-primary">
          <MoreHorizontal className="size-4" />
        </button>
      </div>
    </div>
  );
}
