import { useTranslations } from "next-intl";
import { LivePulseDot } from "@/components/feedback/live-pulse-dot";

export function StatusStrip() {
  const t = useTranslations("statusStrip");
  return (
    <footer className="flex h-7 shrink-0 items-center gap-4 border-t border-border-subtle bg-bg-surface-1 px-4 font-mono text-[11px] text-text-muted">
      <span className="flex items-center gap-1.5">
        {t("ingest")} <LivePulseDot /> {t("healthy")}
      </span>
      <span className="flex items-center gap-1.5">
        {t("models")} <LivePulseDot /> {t("nominal")}
      </span>
      <span>{t("itemsPerHour", { count: 312 })}</span>
      <span>{t("region", { region: "EU-W" })}</span>
      <span className="ml-auto text-text-secondary">v0.9.2-rc · Qalqan AI</span>
    </footer>
  );
}
