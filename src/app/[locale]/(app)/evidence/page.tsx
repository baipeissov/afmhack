import { Database } from "lucide-react";
import { getTranslations } from "next-intl/server";
import { EmptyState } from "@/components/feedback/empty-state";

export default async function EvidenceVault() {
  const t = await getTranslations("emptyState.evidence");
  return <EmptyState icon={Database} title={t("title")} hint={t("hint")} />;
}
