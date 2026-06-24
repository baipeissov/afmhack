"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Search, Settings2 } from "lucide-react";
import { LivePulseDot } from "@/components/feedback/live-pulse-dot";
import { LanguageSwitcher } from "@/components/shell/language-switcher";

export function TopBar() {
  const t = useTranslations("topbar");
  const [clock, setClock] = useState("--:--:--");
  useEffect(() => {
    const tick = () =>
      setClock(
        new Date().toLocaleTimeString("en-GB", { hour12: false })
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="flex h-12 shrink-0 items-center gap-4 border-b border-border-subtle bg-bg-surface-1 px-4">
      <button className="flex w-72 items-center gap-2 rounded-md border border-border-subtle bg-bg-base px-3 py-1.5 text-xs text-text-muted transition-colors hover:border-border-strong">
        <Search className="size-3.5" />
        <span>{t("searchPlaceholder")}</span>
        <kbd className="ml-auto rounded border border-border-strong px-1.5 py-0.5 font-mono text-[10px]">
          ⌘K
        </kbd>
      </button>

      <div className="ml-auto flex items-center gap-4 text-xs text-text-secondary">
        <LanguageSwitcher />
        <span className="font-mono tabular-nums text-text-muted">{clock} UTC</span>
        <span className="flex items-center gap-1.5">
          <LivePulseDot />
          <span className="font-mono">14</span> {t("agentsActive")}
        </span>
        <button className="text-text-muted transition-colors hover:text-text-primary">
          <Settings2 className="size-4" />
        </button>
        <div className="size-7 rounded-full bg-gradient-to-br from-brand-500 to-brand-600 text-center text-[11px] font-semibold leading-7 text-bg-base">
          YA
        </div>
      </div>
    </header>
  );
}
