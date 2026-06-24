import { FileText } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";

export default function Reports() {
  return (
    <EmptyState
      icon={FileText}
      title="Reports & exports"
      hint="Generated prosecutor dossiers ready for FIU handoff, platform takedown requests and downstream systems."
    />
  );
}
