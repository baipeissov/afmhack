"use client";

import { useState } from "react";
import { caseGraph } from "@/mocks/graph";
import type { GraphNode, EdgeKind, NodeType } from "@/types/graph";
import { cn } from "@/lib/utils";

const NODE_COLOR: Record<NodeType, string> = {
  account: "var(--brand-500)",
  wallet: "var(--viz-4)",
  phone: "var(--viz-2)",
  victim: "var(--text-muted)",
  cluster: "var(--sev-critical)",
  exchange: "var(--viz-3)",
};

const EDGE_COLOR: Record<EdgeKind, string> = {
  money: "var(--viz-4)",
  referral: "var(--text-muted)",
  device: "var(--viz-2)",
  admin: "var(--brand-500)",
  promotes: "var(--viz-3)",
};

const EDGE_DASH: Record<EdgeKind, string> = {
  money: "0",
  referral: "3 2",
  device: "1 2",
  admin: "0",
  promotes: "4 3",
};

function NodeShape({ node, r, color }: { node: GraphNode; r: number; color: string }) {
  const common = { fill: "var(--bg-surface-2)", stroke: color, strokeWidth: 0.5 };
  switch (node.type) {
    case "wallet": // diamond
      return <rect x={-r} y={-r} width={r * 2} height={r * 2} transform="rotate(45)" {...common} />;
    case "phone": // square
      return <rect x={-r} y={-r} width={r * 2} height={r * 2} rx={0.4} {...common} />;
    case "exchange": // rounded rect
      return <rect x={-r * 1.3} y={-r * 0.8} width={r * 2.6} height={r * 1.6} rx={0.6} {...common} />;
    case "cluster": // faint big circle
      return <circle r={r} fill="var(--sev-critical)" fillOpacity={0.08} stroke={color} strokeWidth={0.4} strokeDasharray="1 1" />;
    case "account": {
      // hexagon
      const pts = Array.from({ length: 6 }, (_, i) => {
        const a = (Math.PI / 3) * i - Math.PI / 6;
        return `${(Math.cos(a) * r).toFixed(2)},${(Math.sin(a) * r).toFixed(2)}`;
      }).join(" ");
      return <polygon points={pts} {...common} />;
    }
    default: // victim circle
      return <circle r={r} {...common} />;
  }
}

export function KnowledgeGraph() {
  const [sel, setSel] = useState<GraphNode>(
    caseGraph.nodes.find((n) => n.target) ?? caseGraph.nodes[0]
  );
  const byId = (id: string) => caseGraph.nodes.find((n) => n.id === id)!;
  const neighbors = new Set(
    caseGraph.edges
      .filter((e) => e.source === sel.id || e.target === sel.id)
      .flatMap((e) => [e.source, e.target])
  );

  return (
    <div className="flex h-full">
      <div className="relative min-w-0 flex-1 bg-bg-base">
        <svg viewBox="0 0 100 100" className="h-full w-full" preserveAspectRatio="xMidYMid meet">
          {/* edges */}
          {caseGraph.edges.map((e, i) => {
            const s = byId(e.source);
            const t = byId(e.target);
            const active = sel.id === e.source || sel.id === e.target;
            return (
              <line
                key={i}
                x1={s.x}
                y1={s.y}
                x2={t.x}
                y2={t.y}
                stroke={EDGE_COLOR[e.kind]}
                strokeWidth={(e.weight ?? 1) * 0.18 + 0.12}
                strokeDasharray={EDGE_DASH[e.kind]}
                strokeOpacity={active ? 0.9 : 0.28}
              />
            );
          })}
          {/* nodes */}
          {caseGraph.nodes.map((n) => {
            const r = 1.6 + n.centrality * 3.2;
            const dim = !neighbors.has(n.id) && n.id !== sel.id;
            return (
              <g
                key={n.id}
                transform={`translate(${n.x} ${n.y})`}
                className="cursor-pointer"
                opacity={dim ? 0.35 : 1}
                onClick={() => setSel(n)}
              >
                {(n.target || sel.id === n.id) && (
                  <circle r={r + 1.4} fill="none" stroke={NODE_COLOR[n.type]} strokeWidth={0.3} strokeOpacity={0.6} />
                )}
                <NodeShape node={n} r={r} color={NODE_COLOR[n.type]} />
                {n.type !== "victim" && (
                  <text
                    y={r + 2.6}
                    textAnchor="middle"
                    fill="var(--text-secondary)"
                    style={{ fontSize: 2, fontFamily: "var(--font-mono)" }}
                  >
                    {n.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* legend */}
        <div className="absolute bottom-3 left-3 flex flex-wrap gap-x-4 gap-y-1 rounded-md border border-border-subtle bg-bg-surface-1/90 px-3 py-2 text-[10px] text-text-muted backdrop-blur">
          <span>⬡ account</span>
          <span>◆ wallet</span>
          <span>▢ phone</span>
          <span>● victim</span>
          <span>▒ cluster</span>
          <span className="text-text-secondary">edge = money / referral / device</span>
        </div>
      </div>

      {/* inspector */}
      <aside className="hidden w-64 shrink-0 overflow-y-auto border-l border-border-subtle bg-bg-surface-1 p-4 lg:block">
        <div className="text-[10px] font-medium uppercase tracking-[0.08em] text-text-muted">
          Node inspector
        </div>
        <div className="mt-2 font-mono text-sm text-text-primary">{sel.label}</div>
        <div className="mt-0.5 text-xs uppercase tracking-wide text-text-muted">
          {sel.type}
          {sel.target && " · TARGET"}
        </div>
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-[11px] text-text-muted">
            <span>centrality</span>
            <span className="font-mono">{sel.centrality.toFixed(2)}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-bg-surface-3">
            <div className="h-full rounded-full bg-brand-500" style={{ width: `${sel.centrality * 100}%` }} />
          </div>
        </div>
        <div className="mt-3 text-xs text-text-secondary">
          {[...neighbors].filter((n) => n !== sel.id).length} connected edges
        </div>
        {sel.target && (
          <div className="mt-4 space-y-1.5 border-t border-border-subtle pt-3 text-xs text-text-secondary">
            <div className="text-[10px] uppercase tracking-wide text-text-muted">Evidence</div>
            <div>12 messages · 3 clips · 1 wallet</div>
          </div>
        )}
      </aside>
    </div>
  );
}
