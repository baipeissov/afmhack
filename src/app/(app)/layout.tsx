import { Toaster } from "sonner";
import { NavRail } from "@/components/shell/nav-rail";
import { TopBar } from "@/components/shell/top-bar";
import { StatusStrip } from "@/components/shell/status-strip";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg-base">
      <NavRail />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
        <StatusStrip />
      </div>
      <Toaster
        theme="dark"
        position="top-right"
        toastOptions={{
          style: {
            background: "var(--bg-surface-2)",
            border: "1px solid var(--border-strong)",
            color: "var(--text-primary)",
          },
        }}
      />
    </div>
  );
}
