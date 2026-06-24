"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { agentScript } from "@/mocks/agents-script";
import type { ChatMessage } from "@/types/investigation";

export interface CrossSignal {
  id: string;
  topic: string;
  with: string;
  quote: string;
}

export interface StreamState {
  messages: Record<string, ChatMessage[]>;
  typing: Record<string, boolean>;
  signals: CrossSignal[];
  msgCount: number;
  flagCount: number;
  running: boolean;
  finished: boolean;
}

/**
 * Fraud confidence derived from accumulated evidence: each manipulation flag
 * and each cross-thread contradiction pushes it up from a low baseline.
 */
export function deriveConfidence(s: StreamState): number {
  const base = 0.4;
  const v = base + s.flagCount * 0.08 + s.signals.length * 0.18;
  return Math.min(0.94, v);
}

const AGENT_IDS = ["a_03", "a_07", "a_11"];

function emptyState(): StreamState {
  return {
    messages: { a_03: [], a_07: [], a_11: [] },
    typing: {},
    signals: [],
    msgCount: 0,
    flagCount: 0,
    running: false,
    finished: false,
  };
}

/**
 * Replays the scripted multi-agent interrogation with realistic delays and
 * "typing…" indicators. Returns live state plus play/pause/reset controls.
 */
export function useAgentStream() {
  const [state, setState] = useState<StreamState>(emptyState);
  const [paused, setPaused] = useState(false);
  const idx = useRef(0);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  };

  const schedule = useCallback(() => {
    clearTimers();
    if (idx.current >= agentScript.length) {
      setState((s) => ({ ...s, running: false, finished: true }));
      return;
    }
    const step = agentScript[idx.current];
    // show typing for this agent, then drop the message
    const t1 = setTimeout(() => {
      setState((s) => ({ ...s, typing: { ...s.typing, [step.agentId]: true }, running: true }));
      const t2 = setTimeout(() => {
        setState((s) => {
          const msg: ChatMessage = { ...step.message, id: `${step.agentId}-${idx.current}` };
          const next: StreamState = {
            ...s,
            typing: { ...s.typing, [step.agentId]: false },
            messages: {
              ...s.messages,
              [step.agentId]: [...(s.messages[step.agentId] ?? []), msg],
            },
            msgCount: s.msgCount + 1,
            flagCount: s.flagCount + (step.message.flag ? 1 : 0),
          };
          if (step.contradiction) next.signals = [...s.signals, step.contradiction];
          return next;
        });
        idx.current += 1;
        schedule();
      }, 700);
      timers.current.push(t2);
    }, step.delay);
    timers.current.push(t1);
  }, []);

  useEffect(() => {
    if (!paused) schedule();
    return clearTimers;
  }, [paused, schedule]);

  const reset = useCallback(() => {
    clearTimers();
    idx.current = 0;
    setState(emptyState());
    setPaused(false);
  }, []);

  const togglePause = useCallback(() => setPaused((p) => !p), []);

  return { state, paused, togglePause, reset, agentIds: AGENT_IDS };
}
