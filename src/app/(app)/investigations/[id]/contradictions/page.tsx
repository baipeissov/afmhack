"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Plus, Play } from "lucide-react";
import { getCaseForDisplay } from "@/mocks/investigations";
import { techniqueLabels } from "@/mocks/agents-script";
import { SeverityBadge } from "@/components/data/severity-badge";
import { fmtConf, cn } from "@/lib/utils";
import type { Contradiction } from "@/types/investigation";

const AGENTS = ["a_03", "a_07", "a_11", "a_02"];

export default function Contradictions() {
  const { id } = useParams<{ id: string }>();
  const inv = getCaseForDisplay(id);
  const list = inv?.contradictionList ?? [];
  const [selected, setSelected] = useState<Contradiction | null>(list[0] ?? null);

  // build topic → per-agent quote lookup
  const topics = list.map((c) => {
    const cells: Record<string, string> = {};
    cells[c.a.agentId] = c.a.quote;
    cells[c.b.agentId] = c.b.quote;
    return { c, cells };
  });

  return (
    <div className="flex h-full flex-col overflow-y-auto p-6">
      <div className="mb-4 border-b border-border-subtle pb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold tracking-tight text-text-primary">
            Where the story falls apart
          </h2>
          <span className="text-xs text-text-muted">
            {inv?.contradictions ?? 0} lies caught · {list.length} shown below
          </span>
        </div>
        <p className="mt-1 max-w-2xl text-sm text-text-secondary">
          Each row is a question. Each column is an agent. When the suspect gave
          different agents conflicting answers, those cells turn{" "}
          <span className="text-contradiction">purple</span> — that&apos;s a caught lie.
          Click a row to see the proof.
        </p>
      </div>

      {/* matrix */}
      <div className="overflow-hidden rounded-lg border border-border-subtle">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-subtle bg-bg-surface-2 text-left text-[11px] uppercase tracking-wide text-text-muted">
              <th className="px-3 py-2 font-medium">Topic</th>
              {AGENTS.map((a) => (
                <th key={a} className="px-3 py-2 font-mono font-medium">
                  {a}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {topics.map(({ c, cells }) => (
              <tr
                key={c.id}
                onClick={() => setSelected(c)}
                className={cn(
                  "cursor-pointer transition-colors hover:bg-bg-surface-3",
                  selected?.id === c.id && "bg-bg-surface-3"
                )}
              >
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={c.severity} label="" />
                    <span className="text-text-primary">{c.topic}</span>
                  </div>
                </td>
                {AGENTS.map((a) => {
                  const involved = a === c.a.agentId || a === c.b.agentId;
                  return (
                    <td key={a} className="px-3 py-2.5">
                      {cells[a] ? (
                        <span
                          className={cn(
                            "text-xs",
                            involved ? "text-contradiction" : "text-text-secondary"
                          )}
                        >
                          {involved && "● "}&ldquo;{cells[a]}&rdquo;
                        </span>
                      ) : (
                        <span className="text-text-muted">—</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* selected detail */}
      {selected && (
        <div className="mt-4 rounded-lg border border-border-subtle bg-bg-surface-1">
          <div className="flex items-center justify-between border-b border-border-subtle px-4 py-2.5">
            <div className="flex items-center gap-3">
              <span className="text-[11px] uppercase tracking-wide text-text-muted">
                Selected contradiction
              </span>
              <span className="text-sm text-text-primary">{selected.topic}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs text-text-muted">
                confidence {fmtConf(selected.confidence)}
              </span>
              <SeverityBadge severity={selected.severity} />
            </div>
          </div>
          <div className="grid grid-cols-1 divide-y divide-border-subtle md:grid-cols-2 md:divide-x md:divide-y-0">
            {[selected.a, selected.b].map((side) => (
              <div key={side.agentId} className="p-4">
                <div className="mb-1 flex items-center gap-2 font-mono text-[11px] text-text-muted">
                  {side.agentName} · {side.ts}
                </div>
                <p className="text-sm text-text-primary">&ldquo;{side.quote}&rdquo;</p>
                <button className="mt-2 flex items-center gap-1.5 text-xs text-brand-400 hover:underline">
                  <Play className="size-3" /> play clip · source msg
                </button>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between border-t border-border-subtle px-4 py-2.5">
            <span className="text-xs text-text-muted">
              Manipulation technique:{" "}
              <span className="font-medium uppercase text-manipulation">
                {selected.technique.map((t) => techniqueLabels[t]).join(" + ")}
              </span>
            </span>
            <button className="flex items-center gap-1.5 rounded-md border border-border-strong px-2.5 py-1 text-xs text-text-secondary hover:text-text-primary">
              <Plus className="size-3.5" /> Add to report
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
