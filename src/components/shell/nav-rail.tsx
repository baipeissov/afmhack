"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid,
  Radar,
  Crosshair,
  Hexagon,
  Share2,
  BarChart3,
  Bot,
  Database,
  FileText,
  Settings,
  Plus,
  ShieldHalf,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { LivePulseDot } from "@/components/feedback/live-pulse-dot";

const NAV = [
  { href: "/command", label: "Command", icon: LayoutGrid },
  { href: "/detections", label: "Detections", icon: Radar },
  { href: "/investigations", label: "Investigations", icon: Crosshair },
  { href: "/entities", label: "Entities", icon: Hexagon },
  { href: "/investigations/CASE-2041/graph", label: "Graph", icon: Share2 },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/evidence", label: "Vault", icon: Database },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Admin", icon: Settings },
];

export function NavRail() {
  const pathname = usePathname();
  return (
    <nav className="flex h-full w-56 shrink-0 flex-col border-r border-border-subtle bg-bg-surface-1">
      <Link
        href="/command"
        className="flex h-12 items-center gap-2 border-b border-border-subtle px-4"
      >
        <ShieldHalf className="size-5 text-brand-500" />
        <span className="text-sm font-semibold tracking-tight text-text-primary">
          SwarmShield<span className="text-brand-500"> AI</span>
        </span>
      </Link>

      <div className="flex-1 overflow-y-auto py-2">
        {NAV.map((item) => {
          const active =
            pathname === item.href ||
            (item.href !== "/command" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "relative mx-2 flex items-center gap-3 rounded-md px-2.5 py-2 text-[13px] transition-colors",
                active
                  ? "bg-bg-surface-3 text-text-primary"
                  : "text-text-secondary hover:bg-bg-surface-2 hover:text-text-primary"
              )}
            >
              {active && (
                <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-brand-500" />
              )}
              <Icon className="size-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </div>

      <div className="border-t border-border-subtle p-3">
        <Link
          href="/investigations"
          className="flex items-center justify-center gap-2 rounded-md bg-brand-500 px-3 py-2 text-[13px] font-semibold text-bg-base transition-colors hover:bg-brand-400"
        >
          <Plus className="size-4" /> New case
        </Link>
        <div className="mt-3 flex items-center gap-2 px-1 text-[11px] text-text-muted">
          <LivePulseDot /> system nominal
        </div>
      </div>
    </nav>
  );
}
