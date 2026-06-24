import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { FileDown, Download, Share2, PenLine, ShieldCheck } from "lucide-react";
import { getCaseForDisplay } from "@/mocks/investigations";
import { techniqueLabels } from "@/mocks/agents-script";
import { SeverityBadge } from "@/components/data/severity-badge";
import { fmtConf } from "@/lib/utils";

const TOC_KEYS = ["verdict", "summary", "evidence", "techniques", "network", "timeline", "appendix"] as const;

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const inv = getCaseForDisplay(id);
  if (!inv) notFound();
  const r = inv.report;
  const t = await getTranslations("report");

  const EXPORT_BUTTONS = [
    { icon: FileDown, label: t("pdf") },
    { icon: Download, label: t("json") },
    { icon: Share2, label: t("share") },
    { icon: PenLine, label: t("sign") },
  ];

  return (
    <div className="flex h-full overflow-hidden">
      {/* TOC */}
      <aside className="hidden w-56 shrink-0 overflow-y-auto border-r border-border-subtle bg-bg-surface-1 p-4 md:block">
        <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.08em] text-text-muted">
          {t("contents")}
        </div>
        <nav className="space-y-1 text-sm">
          {TOC_KEYS.map((key, i) => (
            <div
              key={key}
              className={i === 0 ? "text-text-primary" : "text-text-secondary hover:text-text-primary"}
            >
              ▸ {t(`toc.${key}`)}
            </div>
          ))}
        </nav>
        <div className="mt-4 space-y-1 border-t border-border-subtle pt-3 text-xs">
          <div className="text-[10px] uppercase tracking-wide text-text-muted">
            {t("evidence")} · {inv.contradictions}
          </div>
          <div className="flex justify-between text-text-secondary">
            <span className="text-sev-critical">● CRIT</span> <span className="font-mono">12</span>
          </div>
          <div className="flex justify-between text-text-secondary">
            <span className="text-sev-high">● HIGH</span> <span className="font-mono">21</span>
          </div>
          <div className="flex justify-between text-text-secondary">
            <span className="text-sev-medium">○ MED</span> <span className="font-mono">14</span>
          </div>
        </div>
      </aside>

      {/* body */}
      <div className="min-w-0 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between border-b border-border-subtle bg-bg-surface-1 px-5 py-2.5">
          <span className="text-sm font-semibold uppercase tracking-wide text-text-secondary">
            {t("headerTitle")}
          </span>
          <div className="flex items-center gap-2 text-xs">
            {EXPORT_BUTTONS.map((b) => (
              <button
                key={b.label}
                className="flex items-center gap-1.5 rounded-md border border-border-strong px-2.5 py-1 text-text-secondary hover:text-text-primary"
              >
                <b.icon className="size-3.5" /> {b.label}
              </button>
            ))}
          </div>
        </div>

        <div className="mx-auto max-w-3xl space-y-6 p-6">
          {/* verdict */}
          <div className="rounded-lg border border-sev-critical/40 bg-sev-critical/5 p-4">
            <div className="flex items-center justify-between">
              <span className="text-base font-semibold text-sev-critical">{r.verdict}</span>
              <span className="font-mono text-sm text-sev-critical">
                {t("confidence")} {fmtConf(inv.confidence)}
              </span>
            </div>
            <p className="mt-1 text-xs text-text-muted">
              {t("target")} {inv.target} · {t("agentSwarm", { count: inv.agentsTotal })} · {t("contradictionsCount", { count: inv.contradictions })}
            </p>
            <p className="mt-2 text-sm text-text-secondary">
              <span className="font-medium text-text-primary">{t("recommendation")}: </span>
              {r.recommendation}
            </p>
          </div>

          {/* summary */}
          <section>
            <h3 className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-text-muted">
              {t("executiveSummary")}
            </h3>
            <p className="text-sm leading-relaxed text-text-secondary">{r.summary}</p>
          </section>

          {/* counts */}
          <section className="space-y-3">
            <h3 className="text-[11px] font-medium uppercase tracking-[0.08em] text-text-muted">
              {t("countsFindings")}
            </h3>
            {r.counts.map((c, i) => (
              <div key={c.id} className="rounded-lg border border-border-subtle bg-bg-surface-1 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-text-primary">
                    {t("count", { n: i + 1 })} ·{" "}
                    <span className="uppercase text-manipulation">
                      {techniqueLabels[c.technique]}
                    </span>
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-text-muted">{t("conf")} {fmtConf(c.confidence)}</span>
                    <SeverityBadge severity={c.severity} />
                  </div>
                </div>
                <p className="mt-1.5 text-sm text-text-secondary">{c.summary}</p>
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  <span className="text-[11px] text-text-muted">{t("exhibits")}:</span>
                  {c.exhibits.map((e) => (
                    <span
                      key={e}
                      className="rounded border border-border-strong px-1.5 py-0.5 font-mono text-[10px] text-evidence"
                    >
                      {e}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </section>

          {/* chain of custody */}
          <section className="flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-surface-1 px-4 py-3 text-xs text-text-secondary">
            <ShieldCheck className="size-4 text-sev-low" />
            <span className="font-medium text-text-primary">{t("chainOfCustody")}:</span>
            {t("artifactsHashed", { count: inv.contradictions })} · {t("modelVersion")} · {t("signOffPending")}
          </section>
        </div>
      </div>
    </div>
  );
}
