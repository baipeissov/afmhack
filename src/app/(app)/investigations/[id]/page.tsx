import Link from "next/link";
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

  return (
    <div className="grid h-full grid-cols-1 gap-4 overflow-y-auto p-5 xl:grid-cols-[1.7fr_1fr]">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Case summary</CardTitle>
            <span className="text-[11px] uppercase tracking-wide text-sev-high">
              {inv.stage.replace("-", " ")}
            </span>
          </CardHeader>
          <CardBody className="space-y-3">
            <div>
              <div className="mb-1 flex justify-between text-xs text-text-muted">
                <span>Confidence</span>
                <span>{inv.agentsDone}/{inv.agentsTotal} agents complete</span>
              </div>
              <ConfidenceMeter value={inv.confidence} />
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-xs text-text-muted">Scheme</dt>
                <dd className="text-text-primary">Financial pyramid (Ponzi)</dd>
              </div>
              <div>
                <dt className="text-xs text-text-muted">Lead theory</dt>
                <dd className="text-text-primary">{inv.leadTheory}</dd>
              </div>
            </dl>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Agent progress</CardTitle>
          </CardHeader>
          <div className="divide-y divide-border-subtle">
            {inv.threads.map((t) => (
              <div key={t.agent.id} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                <span className="flex w-28 items-center gap-1.5">
                  {t.agent.state === "live" && <LivePulseDot />}
                  <span className="font-mono text-text-primary">{t.agent.id}</span>
                </span>
                <span className="w-28 text-xs text-text-muted">{t.agent.persona}</span>
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-bg-surface-3">
                  <div
                    className="h-full rounded-full bg-brand-500"
                    style={{ width: `${t.agent.progress * 100}%` }}
                  />
                </div>
                <span className="w-20 text-right text-xs text-text-muted">
                  {t.agent.state === "done" ? "done" : "live"} · {t.agent.messages} msgs
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Key findings · auto-surfaced</CardTitle>
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
            <CardTitle>Target</CardTitle>
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="font-semibold text-text-primary">{inv.target}</div>
            <div className="text-xs text-text-muted">
              {inv.platform} · {inv.followers} · joined 4mo ago
            </div>
            <Link
              href={`/investigations/${inv.id}/graph`}
              className="inline-flex items-center gap-1.5 text-xs text-brand-400 hover:underline"
            >
              ⬡ 6 linked entities →
            </Link>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk factors</CardTitle>
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
              <TriangleAlert className="size-3.5" /> {inv.contradictions} contradictions detected
            </Link>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-brand-400">
              <Sparkles className="size-3.5" /> Next best action · AI
            </CardTitle>
          </CardHeader>
          <CardBody className="space-y-2 text-sm text-text-secondary">
            <div className="flex items-start gap-2">
              <span className="text-brand-500">▸</span> Deploy 2 more agents on payout-mechanics angle
            </div>
            <div className="flex items-start gap-2">
              <span className="text-brand-500">▸</span> Pull wallet 0x4a3f…e1 transaction history
            </div>
          </CardBody>
        </Card>

        <div className="flex gap-2">
          <Link
            href={`/investigations/${inv.id}/agents`}
            className="flex flex-1 items-center justify-center gap-2 rounded-md border border-border-strong px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-bg-surface-3 hover:text-text-primary"
          >
            <Plus className="size-4" /> Deploy agents
          </Link>
          <Link
            href={`/investigations/${inv.id}/report`}
            className="flex flex-1 items-center justify-center gap-2 rounded-md bg-brand-500 px-3 py-2 text-sm font-semibold text-bg-base transition-colors hover:bg-brand-400"
          >
            <FileDown className="size-4" /> Report
          </Link>
        </div>
      </div>
    </div>
  );
}
