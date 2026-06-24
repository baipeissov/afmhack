import { Bot } from "lucide-react";
import { getTranslations } from "next-intl/server";
import { EmptyState } from "@/components/feedback/empty-state";

export default async function AgentsFleet() {
  const t = await getTranslations("emptyState.agents");
  return <EmptyState icon={Bot} title={t("title")} hint={t("hint")} />;
}
