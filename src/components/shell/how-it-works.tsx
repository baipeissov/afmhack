import { useTranslations } from "next-intl";
import { Radar, Crosshair, MessagesSquare, Gavel, ArrowRight } from "lucide-react";

const STEPS = [
  { key: "detect", icon: Radar },
  { key: "investigate", icon: Crosshair },
  { key: "crossExamine", icon: MessagesSquare },
  { key: "verdict", icon: Gavel },
] as const;

export function HowItWorks() {
  const t = useTranslations("howItWorks");
  return (
    <div className="rounded-lg border border-border-subtle bg-bg-surface-1 p-4">
      <div className="mb-3 text-[11px] font-medium uppercase tracking-[0.08em] text-text-muted">
        {t("heading")}
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((s, i) => (
          <div key={s.key} className="relative flex gap-3">
            <div className="grid size-9 shrink-0 place-items-center rounded-md border border-border-strong bg-bg-base text-brand-400">
              <s.icon className="size-4" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-medium text-text-primary">{t(`${s.key}.title`)}</div>
              <p className="mt-0.5 text-xs leading-relaxed text-text-muted">{t(`${s.key}.text`)}</p>
            </div>
            {i < STEPS.length - 1 && (
              <ArrowRight className="absolute -right-2.5 top-2 hidden size-4 text-border-strong lg:block" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
