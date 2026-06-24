import { LivePulseDot } from "@/components/feedback/live-pulse-dot";

export function StatusStrip() {
  return (
    <footer className="flex h-7 shrink-0 items-center gap-4 border-t border-border-subtle bg-bg-surface-1 px-4 font-mono text-[11px] text-text-muted">
      <span className="flex items-center gap-1.5">
        ingest <LivePulseDot /> healthy
      </span>
      <span className="flex items-center gap-1.5">
        models <LivePulseDot /> nominal
      </span>
      <span>312 items/h</span>
      <span>region EU-W</span>
      <span className="ml-auto text-text-secondary">v0.9.2-rc · SwarmShield AI</span>
    </footer>
  );
}
