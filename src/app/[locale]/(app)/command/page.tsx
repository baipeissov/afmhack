import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { ChevronRight, TriangleAlert, Wallet, FileCheck2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardBody } from "@/components/ui/card";
import { KpiStat } from "@/components/data/kpi-stat";
import { SeverityBadge } from "@/components/data/severity-badge";
import { LivePulseDot, TypingDots } from "@/components/feedback/live-pulse-dot";
import { RiskInflowArea } from "@/components/charts/risk-inflow-area";
import { PageIntro } from "@/components/shell/page-intro";
import { HowItWorks } from "@/components/shell/how-it-works";
import { kpis, schemeMix, liveAgents, alerts } from "@/mocks/dashboard";
import { caseRows } from "@/mocks/investigations";
import { fmtAge, fmtConf } from "@/lib/utils";

const alertIcon = { contradiction: TriangleAlert, wallet: Wallet, report: FileCheck2 };

export default function CommandCenter() {
  const t = useTranslations("command");
  const queue = [...caseRows].sort((a, b) => b.confidence - a.confidence);
  return (
    <div className="flex h-full">
      <div className="min-w-0 flex-1 space-y-5 overflow-y-auto p-6">
        <PageIntro
          title={t("title")}
          lead={t("lead")}
          right={
            <span className="flex items-center gap-2 rounded-md border border-sev-high/40 bg-sev-high/10 px-3 py-1.5 text-sm font-semibold text-sev-high">
              {t("threatLevel")} ▲
            </span>
          }
        />

        <HowItWorks />

        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {kpis.map((k) => (
            <KpiStat key={k.label} {...k} />
          ))}
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.6fr_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>{t("riskInflowTitle")}</CardTitle>
              <span className="font-mono text-[11px] text-text-muted">
                {t("riskInflowSub")}
              </span>
            </CardHeader>
            <CardBody className="pr-2">
              <RiskInflowArea />
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("schemeMixTitle")}</CardTitle>
            </CardHeader>
            <CardBody className="space-y-3">
              {schemeMix.map((s) => (
                <div key={s.scheme}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="text-text-secondary">{s.label}</span>
                    <span className="font-mono tabular-nums text-text-primary">{s.pct}%</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-bg-surface-3">
                    <div
                      className="h-full rounded-full bg-brand-500"
                      style={{ width: `${s.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{t("needsDecisionTitle")}</CardTitle>
            <span className="text-[11px] text-text-muted">{t("needsDecisionSub")}</span>
          </CardHeader>
          <div className="divide-y divide-border-subtle">
            {queue.map((c) => (
              <Link
                key={c.id}
                href={`/investigations/${c.id}`}
                className="group flex items-center gap-4 px-4 py-3 transition-colors hover:bg-bg-surface-3"
              >
                <SeverityBadge severity={c.severity} className="w-16" />
                <span className="w-32 truncate font-medium text-text-primary">
                  {c.target}
                </span>
                <span className="w-20 text-xs uppercase tracking-wide text-text-muted">
                  {c.scheme}
                </span>
                <span className="font-mono text-sm tabular-nums text-text-secondary">
                  {fmtConf(c.confidence)}
                </span>
                <span className="flex items-center gap-1.5 text-xs text-text-secondary">
                  {c.agentsLive && <LivePulseDot />}
                  {c.agentsDone}/{c.agentsTotal} {t("agentsCount")}
                </span>
                <span className="ml-auto font-mono text-xs text-text-muted">
                  {fmtAge(c.ageMinutes)}
                </span>
                <ChevronRight className="size-4 text-text-muted transition-transform group-hover:translate-x-0.5 group-hover:text-text-primary" />
              </Link>
            ))}
          </div>
        </Card>
      </div>

      {/* Live Ops rail */}
      <aside className="hidden w-64 shrink-0 space-y-4 overflow-y-auto border-l border-border-subtle bg-bg-surface-1 p-4 lg:block">
        <div>
          <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.08em] text-text-muted">
            {t("agentsTalkingNow")}
          </div>
          <div className="space-y-2">
            {liveAgents.map((a) => (
              <div
                key={a.id}
                className="flex items-center gap-2 rounded-md border border-border-subtle bg-bg-base px-2.5 py-2 text-xs"
              >
                <LivePulseDot critical={false} />
                <span className="font-mono text-text-primary">{a.id}</span>
                <span className="text-text-muted">{a.case}</span>
                <span className="ml-auto text-text-secondary">
                  {a.state === "typing" ? <TypingDots /> : a.state}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.08em] text-text-muted">
            {t("recentAlerts")}
          </div>
          <div className="space-y-2">
            {alerts.map((al) => {
              const Icon = alertIcon[al.kind];
              return (
                <div
                  key={al.id}
                  className="flex items-start gap-2 rounded-md border border-border-subtle bg-bg-base px-2.5 py-2 text-xs"
                >
                  <Icon className="mt-0.5 size-3.5 shrink-0 text-sev-high" />
                  <span className="text-text-secondary">{al.text}</span>
                </div>
              );
            })}
          </div>
        </div>
      </aside>
    </div>
  );
}
