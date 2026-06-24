import { Settings } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";

export default function SettingsPage() {
  return (
    <EmptyState
      icon={Settings}
      title="Settings & admin"
      hint="Sources, model routing, RBAC and the immutable audit log."
    />
  );
}
