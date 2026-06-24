import { Hexagon } from "lucide-react";
import { getTranslations } from "next-intl/server";
import { EmptyState } from "@/components/feedback/empty-state";

export default async function Entities() {
  const t = await getTranslations("emptyState.entities");
  return <EmptyState icon={Hexagon} title={t("title")} hint={t("hint")} />;
}
