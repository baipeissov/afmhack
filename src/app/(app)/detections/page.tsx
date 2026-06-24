import Link from "next/link";
import { Check, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { SeverityBadge } from "@/components/data/severity-badge";
import { PageIntro } from "@/components/shell/page-intro";
import { detections } from "@/mocks/detections";
import { fmtAge, fmtConf } from "@/lib/utils";

export default function DetectionFeed() {
  return (
    <div className="space-y-5 p-6">
      <PageIntro
        title="Suspicious videos"
        lead="Our AI watches social media and flags videos that look like scams, illegal casinos or pyramid schemes. Review one and promote it to a full investigation."
      />

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {detections.map((d) => (
          <Card key={d.id} className="overflow-hidden">
            <div className="flex items-stretch">
              <div className="w-1 shrink-0" style={{ backgroundColor: `var(--sev-${d.severity})` }} />
              <div className="min-w-0 flex-1 p-3">
                <div className="flex items-center justify-between">
                  <SeverityBadge severity={d.severity} />
                  <span className="font-mono text-xs tabular-nums text-text-secondary">
                    {fmtConf(d.confidence)}
                  </span>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <div className="grid size-10 shrink-0 place-items-center rounded bg-bg-surface-3 text-text-muted">
                    ▶
                  </div>
                  <div className="min-w-0">
                    <div className="truncate font-medium text-text-primary">{d.handle}</div>
                    <div className="text-[11px] text-text-muted">
                      {d.platform} · {d.followers} · {fmtAge(d.ageMinutes)} ago
                    </div>
                  </div>
                </div>
                <div className="mt-2 text-xs uppercase tracking-wide text-text-muted">
                  {d.scheme}
                </div>
                <div className="mt-1 flex items-start gap-1 text-xs text-manipulation">
                  ⚑ {d.flag}
                </div>
                <div className="mt-2 flex items-center gap-2 font-mono text-[10px] text-text-muted">
                  signals: {d.signals} ·{" "}
                  <span className={d.modalities.ocr ? "text-sev-low" : ""}>OCR {d.modalities.ocr ? "✓" : "—"}</span>
                  <span className={d.modalities.asr ? "text-sev-low" : ""}>ASR {d.modalities.asr ? "✓" : "—"}</span>
                  <span className={d.modalities.vision ? "text-sev-low" : ""}>vision {d.modalities.vision ? "✓" : "—"}</span>
                </div>
                <div className="mt-3 flex gap-2 border-t border-border-subtle pt-2.5">
                  <button className="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-border-strong px-2 py-1.5 text-xs text-text-muted hover:text-text-primary">
                    <X className="size-3.5" /> Dismiss
                  </button>
                  <Link
                    href="/investigations/CASE-2041"
                    className="flex flex-1 items-center justify-center gap-1.5 rounded-md bg-brand-500 px-2 py-1.5 text-xs font-semibold text-bg-base hover:bg-brand-400"
                  >
                    <Check className="size-3.5" /> Promote →
                  </Link>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
