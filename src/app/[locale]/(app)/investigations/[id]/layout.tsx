import { notFound } from "next/navigation";
import { CaseHeader } from "@/components/investigation/case-header";
import { CaseTabs } from "@/components/investigation/case-tabs";
import { getCaseForDisplay } from "@/mocks/investigations";

export default async function CaseLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const inv = getCaseForDisplay(id);
  if (!inv) notFound();

  return (
    <div className="flex h-full flex-col">
      <CaseHeader inv={inv} />
      <CaseTabs caseId={inv.id} />
      <div className="min-h-0 flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
