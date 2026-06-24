import { Bot } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";

export default function AgentsFleet() {
  return (
    <EmptyState
      icon={Bot}
      title="Agent fleet"
      hint="Configure agent personas, objectives and model routing. Live swarm activity is shown inside each investigation's War Room."
    />
  );
}
