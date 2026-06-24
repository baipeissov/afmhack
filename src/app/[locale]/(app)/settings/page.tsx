import { Settings } from "lucide-react";
import { getTranslations } from "next-intl/server";
import { EmptyState } from "@/components/feedback/empty-state";

export default async function SettingsPage() {
  const t = await getTranslations("emptyState.settings");
  return <EmptyState icon={Settings} title={t("title")} hint={t("hint")} />;
}
