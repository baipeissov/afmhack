import { Database } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";

export default function EvidenceVault() {
  return (
    <EmptyState
      icon={Database}
      title="Evidence vault"
      hint="Hashed artifacts with full chain-of-custody — clips, transcripts, messages and wallets across all cases."
    />
  );
}
