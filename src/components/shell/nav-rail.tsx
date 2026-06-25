"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { usePathname } from "@/i18n/navigation";
import {
  LayoutGrid,
  Radar,
  Crosshair,
  Hexagon,
  Share2,
  Network,
  BarChart3,
  Bot,
  MessageSquare,
  Send,
  Database,
  FileText,
  Settings,
  Plus,
  ShieldHalf,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { LivePulseDot } from "@/components/feedback/live-pulse-dot";

const NAV = [
  { href: "/command", key: "command", icon: LayoutGrid },
  { href: "/detections", key: "detections", icon: Radar },
  { href: "/investigations", key: "investigations", icon: Crosshair },
  { href: "/entities", key: "entities", icon: Hexagon },
  { href: "/investigations/CASE-2041/graph", key: "graph", icon: Share2 },
  { href: "/network", key: "network", icon: Network },
  { href: "/engagement", key: "engagement", icon: Send },
  { href: "/liaison", key: "liaison", icon: MessageSquare },
  { href: "/analytics", key: "analytics", icon: BarChart3 },
  { href: "/agents", key: "agents", icon: Bot },
  { href: "/evidence", key: "vault", icon: Database },
  { href: "/reports", key: "reports", icon: FileText },
  { href: "/settings", key: "admin", icon: Settings },
] as const;

export function NavRail() {
  const t = useTranslations("nav");
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
              {t(item.key)}
            </Link>
          );
        })}
      </div>

      <div className="border-t border-border-subtle p-3">
        <Link
          href="/investigations"
          className="flex items-center justify-center gap-2 rounded-md bg-brand-500 px-3 py-2 text-[13px] font-semibold text-bg-base transition-colors hover:bg-brand-400"
        >
          <Plus className="size-4" /> {t("newCase")}
        </Link>
        <div className="mt-3 flex items-center gap-2 px-1 text-[11px] text-text-muted">
          <LivePulseDot /> {t("systemNominal")}
        </div>
      </div>
    </nav>
  );
}
