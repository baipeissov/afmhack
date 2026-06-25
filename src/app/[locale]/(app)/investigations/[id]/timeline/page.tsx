import { notFound } from "next/navigation";
import { getCaseForDisplay } from "@/mocks/investigations";
import { techniqueLabels } from "@/mocks/agents-script";
import { SeverityBadge } from "@/components/data/severity-badge";
import { cn } from "@/lib/utils";
import type { TimelineEvent } from "@/types/investigation";

const KIND_STYLE: Record<TimelineEvent["kind"], { glyph: string; color: string }> = {
  detection: { glyph: "●", color: "text-sev-critical" },
  "case-opened": { glyph: "●", color: "text-brand-500" },
  claim: { glyph: "●", color: "text-text-secondary" },
  contradiction: { glyph: "◆", color: "text-contradiction" },
  evidence: { glyph: "◆", color: "text-evidence" },
  technique: { glyph: "●", color: "text-manipulation" },
  milestone: { glyph: "▣", color: "text-sev-critical" },
  "in-progress": { glyph: "◔", color: "text-brand-400" },
};

export default async function TimelinePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const inv = getCaseForDisplay(id);
  if (!inv) notFound();

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-5 border-b border-border-subtle pb-4">
        <h2 className="text-xl font-semibold tracking-tight text-text-primary">
          What happened, step by step
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-text-secondary">
          Qalqan reconstructs the whole case as a timeline — from the first
          flagged video to every lie and piece of evidence the agents uncovered.
        </p>
      </div>

      <ol className="relative ml-2 border-l border-border-strong">
        {inv.timeline.map((ev) => {
          const k = KIND_STYLE[ev.kind];
          return (
            <li key={ev.id} className="relative mb-5 pl-6">
              <span
                className={cn(
                  "absolute -left-[9px] top-0.5 grid size-4 place-items-center rounded-full bg-bg-base text-[10px]",
                  k.color,
                  ev.kind === "in-progress" && "ss-live-dot"
                )}
              >
                {k.glyph}
              </span>
              <div className="flex items-baseline gap-3">
                <span className="w-12 shrink-0 font-mono text-xs text-text-muted">{ev.ts}</span>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-medium uppercase tracking-wide text-text-muted">
                      {ev.kind.replace("-", " ")}
                    </span>
                    {ev.agentName && (
                      <span className="font-mono text-[10px] text-text-muted">({ev.agentName})</span>
                    )}
                    {ev.severity && <SeverityBadge severity={ev.severity} />}
                  </div>
                  <p className="text-sm text-text-primary">{ev.title}</p>
                  {ev.detail && <p className="text-xs text-text-muted">{ev.detail}</p>}
                  {ev.flag && (
                    <span className="mt-0.5 inline-block text-[11px] font-medium text-manipulation">
                      ⚑ {techniqueLabels[ev.flag]}
                    </span>
                  )}
                  {ev.linksTo && (
                    <span className="ml-2 text-[11px] text-text-muted">
                      └─ links to → {inv.timeline.find((t) => t.id === ev.linksTo)?.ts}
                    </span>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>

      <div className="mt-2 flex flex-wrap items-center gap-4 border-t border-border-subtle pt-4 text-xs text-text-muted">
        <span className="flex items-center gap-1.5"><span className="text-contradiction">◆</span> contradiction / evidence</span>
        <span className="flex items-center gap-1.5"><span className="text-manipulation">⚑</span> manipulation tactic</span>
        <span className="flex items-center gap-1.5"><span className="text-sev-critical">▣</span> milestone</span>
      </div>
    </div>
  );
}
