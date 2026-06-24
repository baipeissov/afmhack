"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { Pause, Play, RotateCcw, AlertTriangle, ShieldAlert, Info } from "lucide-react";
import { useAgentStream, deriveConfidence } from "@/hooks/use-agent-stream";
import { TypingDots, LivePulseDot } from "@/components/feedback/live-pulse-dot";
import { VerdictMeter } from "@/components/investigation/verdict-meter";
import { techniqueLabels } from "@/mocks/agents-script";
import { cn } from "@/lib/utils";

// Plain-language description of each agent so a first-time viewer instantly
// understands WHY there are several of them.
const AGENT_META: Record<
  string,
  { name: string; role: string; color: string }
> = {
  a_03: { name: "The Skeptic", role: "Pushes back, asks who guarantees the returns", color: "var(--viz-2)" },
  a_07: { name: "The Eager Newbie", role: "Plays naive to learn how payouts really work", color: "var(--viz-4)" },
  a_11: { name: "The Due-Diligence", role: "Asks for licences and legal proof", color: "var(--viz-3)" },
};

export default function WarRoom() {
  const { state, paused, togglePause, reset, agentIds } = useAgentStream();
  const confidence = deriveConfidence(state);
  const seenSignals = useRef(0);

  // Fire a clear, human notification the moment a contradiction is caught.
  useEffect(() => {
    if (state.signals.length > seenSignals.current) {
      const sig = state.signals[state.signals.length - 1];
      toast.error("Contradiction caught — the suspect just lied", {
        description: `On "${sig.topic}", different agents got opposite answers.`,
        icon: <ShieldAlert className="size-4 text-sev-critical" />,
        duration: 6000,
      });
      seenSignals.current = state.signals.length;
    }
  }, [state.signals]);

  return (
    <div className="flex h-full flex-col">
      {/* plain-language explainer */}
      <div className="flex items-start gap-3 border-b border-border-subtle bg-bg-surface-1 px-5 py-3">
        <Info className="mt-0.5 size-4 shrink-0 text-brand-400" />
        <p className="text-sm text-text-secondary">
          <span className="font-medium text-text-primary">
            Three AI agents are questioning this account at the same time
          </span>{" "}
          — each pretends to be a different kind of investor. SwarmShield compares
          their answers live and{" "}
          <span className="text-contradiction">flags the moment the suspect contradicts itself.</span>
        </p>
        <div className="ml-auto flex shrink-0 items-center gap-2">
          <button
            onClick={togglePause}
            className="flex items-center gap-1.5 rounded-md border border-border-strong px-2.5 py-1.5 text-xs text-text-secondary hover:text-text-primary"
          >
            {paused ? <Play className="size-3.5" /> : <Pause className="size-3.5" />}
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            onClick={reset}
            className="flex items-center gap-1.5 rounded-md bg-brand-500 px-2.5 py-1.5 text-xs font-semibold text-bg-base hover:bg-brand-400"
          >
            <RotateCcw className="size-3.5" /> Replay demo
          </button>
        </div>
      </div>

      {/* verdict meter — the headline number, climbs as evidence lands */}
      <div className="border-b border-border-subtle px-5 py-3">
        <VerdictMeter value={confidence} />
      </div>

      <div className="flex min-h-0 flex-1">
        {/* agent threads */}
        <div className="grid min-w-0 flex-1 grid-cols-1 divide-x divide-border-subtle md:grid-cols-3">
          {agentIds.map((aid) => {
            const meta = AGENT_META[aid];
            const msgs = state.messages[aid] ?? [];
            const typing = state.typing[aid];
            return (
              <div key={aid} className="flex min-h-0 flex-col">
                <div className="border-b border-border-subtle bg-bg-surface-1 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span
                      className="grid size-7 shrink-0 place-items-center rounded-full text-[11px] font-semibold text-bg-base"
                      style={{ backgroundColor: meta.color }}
                    >
                      {aid.slice(-2)}
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 text-sm font-medium text-text-primary">
                        {meta.name}
                        <LivePulseDot />
                      </div>
                      <div className="truncate text-[11px] text-text-muted">{meta.role}</div>
                    </div>
                  </div>
                </div>
                <div className="min-h-0 flex-1 space-y-2.5 overflow-y-auto p-4">
                  {msgs.map((m) => (
                    <div
                      key={m.id}
                      className={cn(
                        "ss-fade-in max-w-[85%] rounded-lg px-3 py-2 text-[13px]",
                        m.speaker === "agent"
                          ? "ml-auto bg-brand-500/15 text-text-primary"
                          : "mr-auto border border-border-subtle bg-bg-surface-2 text-text-secondary"
                      )}
                    >
                      <div className="mb-0.5 text-[10px] font-medium uppercase tracking-wide text-text-muted">
                        {m.speaker === "agent" ? "Agent" : "Suspect"} · {m.ts}
                      </div>
                      {m.text}
                      {m.flag && (
                        <div className="mt-1.5 flex items-center gap-1.5 rounded bg-manipulation/15 px-1.5 py-1 text-[11px] font-medium text-manipulation">
                          <AlertTriangle className="size-3" />
                          Manipulation: {techniqueLabels[m.flag]}
                        </div>
                      )}
                    </div>
                  ))}
                  {typing && (
                    <div className="ml-auto flex w-fit items-center gap-2 rounded-lg bg-brand-500/10 px-3 py-2.5">
                      <TypingDots />
                    </div>
                  )}
                  {msgs.length === 0 && !typing && (
                    <div className="pt-10 text-center text-xs text-text-muted">
                      Agent is making contact…
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* caught-lies rail */}
        <aside className="hidden w-72 shrink-0 flex-col overflow-y-auto border-l border-border-subtle bg-bg-surface-1 p-4 lg:flex">
          <div className="mb-1 text-sm font-semibold text-text-primary">Lies caught</div>
          <p className="mb-3 text-xs text-text-muted">
            When two agents get different answers to the same question, that&apos;s a
            contradiction — strong proof of fraud.
          </p>
          {state.signals.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border-strong p-4 text-center text-xs text-text-muted">
              No lies caught yet.
              <br />
              Agents are still gathering answers…
            </div>
          ) : (
            <div className="space-y-3">
              {state.signals.map((sig, i) => (
                <div
                  key={sig.id}
                  className="ss-flash rounded-lg border border-contradiction/50 bg-contradiction/10 p-3"
                >
                  <div className="flex items-center gap-1.5 text-sm font-semibold text-contradiction">
                    <ShieldAlert className="size-4" /> Lie #{i + 1}: {sig.topic}
                  </div>
                  <div className="mt-1.5 font-mono text-xs text-text-secondary">
                    {sig.quote}
                  </div>
                  <div className="mt-1.5 text-[11px] text-text-muted">
                    Caught because the {sig.with} agent was told the opposite.
                  </div>
                </div>
              ))}
            </div>
          )}
          {state.finished && (
            <div className="mt-4 rounded-lg border border-brand-500/40 bg-brand-500/10 p-3 text-xs text-brand-400">
              ✓ Interrogation complete. Enough evidence to write the report.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
