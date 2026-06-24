import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { Card } from "@/components/ui/card";
import { SeverityBadge } from "@/components/data/severity-badge";
import { PageIntro } from "@/components/shell/page-intro";
import { EmptyState } from "@/components/feedback/empty-state";
import { Inbox } from "lucide-react";
import { DetectionActions } from "@/components/investigation/detection-actions";
import { UploadTestVideo } from "@/components/investigation/upload-test-video";
import { fetchQueue, riskToSeverity, ageMinutesSince } from "@/lib/api";
import { fmtAge, fmtConf } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function DetectionFeed() {
  const t = await getTranslations("detections");
  const queue = await fetchQueue();

  return (
    <div className="space-y-5 p-6">
      <PageIntro title={t("title")} lead={t("lead")} />

      <UploadTestVideo />

      {queue.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title="Очередь пуста"
          hint="Загрузи видео выше — оно пройдёт через полный pipeline (Whisper/OCR/CLIP/fusion) и появится здесь с реальным risk score."
        />
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {queue.map((d) => {
            const severity = riskToSeverity(d.risk_score);
            return (
              <Card key={d.item_id} className="overflow-hidden">
                <div className="flex items-stretch">
                  <div className="w-1 shrink-0" style={{ backgroundColor: `var(--sev-${severity})` }} />
                  <div className="min-w-0 flex-1 p-3">
                    <div className="flex items-center justify-between">
                      <SeverityBadge severity={severity} />
                      <span className="font-mono text-xs tabular-nums text-text-secondary">
                        {fmtConf(d.risk_score)}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="grid size-10 shrink-0 place-items-center rounded bg-bg-surface-3 text-text-muted">
                        ▶
                      </div>
                      <div className="min-w-0">
                        <div className="truncate font-medium text-text-primary">{d.account_handle}</div>
                        <div className="text-[11px] text-text-muted">
                          {d.platform} · {fmtAge(ageMinutesSince(d.discovered_at))} {t("ago")}
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 text-xs uppercase tracking-wide text-text-muted">{d.top_class_ru}</div>
                    {d.explanations[0] && (
                      <div className="mt-1 flex items-start gap-1 text-xs text-manipulation">{d.explanations[0]}</div>
                    )}
                    <div className="mt-2 flex items-center gap-2 font-mono text-[10px] text-text-muted">
                      {t("signals")}: {d.explanations.length} ·{" "}
                      <span className={d.modalities.ocr ? "text-sev-low" : ""}>OCR {d.modalities.ocr ? "✓" : "—"}</span>
                      <span className={d.modalities.asr ? "text-sev-low" : ""}>ASR {d.modalities.asr ? "✓" : "—"}</span>
                      <span className={d.modalities.vision ? "text-sev-low" : ""}>{t("vision")} {d.modalities.vision ? "✓" : "—"}</span>
                    </div>
                    {d.status === "pending_review" ? (
                      <DetectionActions itemId={d.item_id} />
                    ) : (
                      <div className="mt-3 border-t border-border-subtle pt-2.5 text-xs text-text-muted">
                        Статус: <span className="font-medium text-text-primary">{d.status}</span>
                      </div>
                    )}
                    <Link
                      href={`/detections/${d.item_id}`}
                      className="mt-2 block text-center text-[11px] text-brand-400 hover:underline"
                    >
                      Открыть досье →
                    </Link>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
