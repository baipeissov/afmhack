import { Hexagon } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";

export default function Entities() {
  return (
    <EmptyState
      icon={Hexagon}
      title="Entity registry"
      hint="Accounts, channels, wallets and devices surfaced across investigations. Open a case graph to inspect linked entities."
    />
  );
}
