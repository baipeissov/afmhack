import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { MoreHorizontal } from "lucide-react";
import { SeverityBadge } from "@/components/data/severity-badge";
import { LivePulseDot } from "@/components/feedback/live-pulse-dot";
import { PageIntro } from "@/components/shell/page-intro";
import { caseRows } from "@/mocks/investigations";
import { fmtAge, fmtConf } from "@/lib/utils";

const COL_KEYS = ["risk", "case", "target", "scheme", "confidence", "agents", "lies", "age"] as const;

export default function InvestigationsList() {
  const t = useTranslations("investigationsList");
  return (
    <div className="space-y-5 p-6">
      <PageIntro title={t("title")} lead={t("lead")} />

      <div className="overflow-hidden rounded-lg border border-border-subtle">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-subtle bg-bg-surface-2 text-left text-[10px] uppercase tracking-[0.08em] text-text-muted">
              {COL_KEYS.map((c) => (
                <th key={c} className="px-4 py-2.5 font-medium">
                  {t(`columns.${c}`)}
                </th>
              ))}
              <th className="px-4 py-2.5 font-medium" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {caseRows.map((c) => (
              <tr key={c.id} className="group transition-colors hover:bg-bg-surface-3">
                <td className="px-4 py-3">
                  <SeverityBadge severity={c.severity} />
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/investigations/${c.id}`}
                    className="font-mono text-brand-400 hover:underline"
                  >
                    {c.id}
                  </Link>
                </td>
                <td className="px-4 py-3 font-medium text-text-primary">{c.target}</td>
                <td className="px-4 py-3 text-xs uppercase tracking-wide text-text-secondary">
                  {c.scheme}
                </td>
                <td className="px-4 py-3 font-mono tabular-nums text-text-secondary">
                  {fmtConf(c.confidence)}
                </td>
                <td className="px-4 py-3">
                  <span className="flex items-center gap-1.5 font-mono text-xs tabular-nums text-text-secondary">
                    {c.agentsLive && <LivePulseDot />}
                    {c.agentsDone}/{c.agentsTotal}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono tabular-nums text-text-secondary">
                  {c.contradictions}
                </td>
                <td className="px-4 py-3 font-mono text-xs tabular-nums text-text-muted">
                  {fmtAge(c.ageMinutes)}
                </td>
                <td className="px-4 py-3 text-right">
                  <button className="text-text-muted opacity-0 transition-opacity hover:text-text-primary group-hover:opacity-100">
                    <MoreHorizontal className="size-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
