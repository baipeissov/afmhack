"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";

const LOCALE_LABEL: Record<string, string> = {
  ru: "RU",
  kk: "KK",
  en: "EN",
};

export function LanguageSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="flex items-center gap-1 rounded-md border border-border-subtle bg-bg-base p-0.5 text-[11px] font-medium">
      {routing.locales.map((l) => (
        <button
          key={l}
          onClick={() => router.replace(pathname, { locale: l })}
          className={
            l === locale
              ? "rounded px-2 py-1 bg-brand-500 text-bg-base"
              : "rounded px-2 py-1 text-text-muted transition-colors hover:text-text-primary"
          }
        >
          {LOCALE_LABEL[l]}
        </button>
      ))}
    </div>
  );
}
