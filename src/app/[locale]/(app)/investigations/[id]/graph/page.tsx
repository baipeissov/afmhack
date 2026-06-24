import { useTranslations } from "next-intl";
import { KnowledgeGraph } from "@/components/graph/knowledge-graph";

export default function GraphPage() {
  const t = useTranslations("graph");
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-border-subtle bg-bg-surface-1 px-5 py-3">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">
            {t("heading")}
          </h2>
          <p className="text-xs text-text-muted">
            {t("lead")}
          </p>
        </div>
        <div className="ml-auto hidden items-center gap-2 text-xs text-text-muted md:flex">
          <span className="rounded border border-brand-500/40 bg-brand-500/10 px-2 py-1 text-brand-400">
            {t("networkView")}
          </span>
          <span className="rounded border border-border-strong px-2 py-1">{t("mapView")}</span>
        </div>
      </div>
      <div className="min-h-0 flex-1">
        <KnowledgeGraph />
      </div>
    </div>
  );
}
