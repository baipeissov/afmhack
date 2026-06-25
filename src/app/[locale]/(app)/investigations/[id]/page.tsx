import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { Check, TriangleAlert, Sparkles, Plus, FileDown } from "lucide-react";
import { notFound } from "next/navigation";
import { Card, CardHeader, CardTitle, CardBody } from "@/components/ui/card";
import { ConfidenceMeter } from "@/components/data/confidence-meter";
import { LivePulseDot } from "@/components/feedback/live-pulse-dot";
import { getCaseForDisplay } from "@/mocks/investigations";

export default async function CaseOverview({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const inv = getCaseForDisplay(id);
  if (!inv) notFound();
  const t = await getTranslations("caseOverview");

  return (
    <div className="grid h-full grid-cols-1 gap-4 overflow-y-auto p-5 xl:grid-cols-[1.7fr_1fr]">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>{t("caseSummary")}</CardTitle>
            <span className="text-[11px] uppercase tracking-wide text-sev-high">
              {inv.stage.replace("-", " ")}
            </span>
          </CardHeader>
          <CardBody className="space-y-3">
            <div>
              <div className="mb-1 flex justify-between text-xs text-text-muted">
                <span>{t("confidence")}</span>
                <span>{inv.agentsDone}/{inv.agentsTotal} {t("agentsComplete")}</span>
              </div>
              <ConfidenceMeter value={inv.confidence} />
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-xs text-text-muted">{t("scheme")}</dt>
                <dd className="text-text-primary">{t("schemePyramid")}</dd>
              </div>
              <div>
                <dt className="text-xs text-text-muted">{t("leadTheory")}</dt>
                <dd className="text-text-primary">{inv.leadTheory}</dd>
              </div>
            </dl>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("agentProgress")}</CardTitle>
          </CardHeader>
          <div className="divide-y divide-border-subtle">
            {inv.threads.map((th) => (
              <div key={th.agent.id} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                <span className="flex w-28 items-center gap-1.5">
                  {th.agent.state === "live" && <LivePulseDot />}
                  <span className="font-mono text-text-primary">{th.agent.id}</span>
                </span>
                <span className="w-28 text-xs text-text-muted">{th.agent.persona}</span>
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-bg-surface-3">
                  <div
                    className="h-full rounded-full bg-brand-500"
                    style={{ width: `${th.agent.progress * 100}%` }}
                  />
                </div>
                <span className="w-20 text-right text-xs text-text-muted">
                  {th.agent.state === "done" ? t("statusDone") : t("statusLive")} · {th.agent.messages} {t("msgs")}
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("keyFindings")}</CardTitle>
          </CardHeader>
          <CardBody className="space-y-2">
            {inv.findings.map((f) => (
              <div key={f.id} className="flex items-start gap-2 text-sm text-text-secondary">
                <span className="mt-1.5 size-1 shrink-0 rounded-full bg-brand-500" />
                {f.text}
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      {/* Dossier */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>{t("target")}</CardTitle>
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="font-semibold text-text-primary">{inv.target}</div>
            <div className="text-xs text-text-muted">
              {inv.platform} · {inv.followers} · {t("joined")}
            </div>
            <Link
              href="/network"
              className="inline-flex items-center gap-1.5 text-xs text-brand-400 hover:underline"
            >
              ⬡ {t("linkedEntities", { count: 6 })} →
            </Link>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("riskFactors")}</CardTitle>
          </CardHeader>
          <CardBody className="space-y-2">
            {inv.riskFactors.map((r) => (
              <div key={r.label} className="flex items-start gap-2 text-sm text-text-secondary">
                <Check className="mt-0.5 size-3.5 shrink-0 text-sev-low" />
                {r.label}
              </div>
            ))}
            <Link
              href={`/investigations/${inv.id}/contradictions`}
              className="mt-2 flex items-center gap-2 border-t border-border-subtle pt-3 text-sm text-sev-high hover:underline"
            >
              <TriangleAlert className="size-3.5" /> {t("contradictionsDetected", { count: inv.contradictions })}
            </Link>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-brand-400">
              <Sparkles className="size-3.5" /> {t("nextBestAction")}
            </CardTitle>
          </CardHeader>
          <CardBody className="space-y-2 text-sm text-text-secondary">
            <div className="flex items-start gap-2">
              <span className="text-brand-500">▸</span> {t("actionDeployAgents")}
            </div>
            <div className="flex items-start gap-2">
              <span className="text-brand-500">▸</span> {t("actionPullWallet")}
            </div>
          </CardBody>
        </Card>

        <div className="flex gap-2">
          <Link
            href={`/investigations/${inv.id}/agents`}
            className="flex flex-1 items-center justify-center gap-2 rounded-md border border-border-strong px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-bg-surface-3 hover:text-text-primary"
          >
            <Plus className="size-4" /> {t("deployAgentsButton")}
          </Link>
          <Link
            href={`/investigations/${inv.id}/report`}
            className="flex flex-1 items-center justify-center gap-2 rounded-md bg-brand-500 px-3 py-2 text-sm font-semibold text-bg-base transition-colors hover:bg-brand-400"
          >
            <FileDown className="size-4" /> {t("reportButton")}
          </Link>
        </div>
      </div>
    </div>
  );
}
