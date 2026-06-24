import { FileText } from "lucide-react";
import { getTranslations } from "next-intl/server";
import { EmptyState } from "@/components/feedback/empty-state";

export default async function Reports() {
  const t = await getTranslations("emptyState.reports");
  return <EmptyState icon={FileText} title={t("title")} hint={t("hint")} />;
}
