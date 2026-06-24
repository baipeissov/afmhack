"use client";

import { useRef, useState } from "react";
import { useRouter } from "@/i18n/navigation";
import { Upload } from "lucide-react";
import { analyzeVideo } from "@/lib/api";

/** Ручной запуск анализа из дашборда — для теста pipeline без поднятого
 * Collector'а: загружаешь видео, оно сразу проходит через Component A/B
 * и появляется в списке ниже с реальным risk score. */
export function UploadTestVideo() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [handle, setHandle] = useState("@test.account");
  const [ageDays, setAgeDays] = useState(23);
  const [growth, setGrowth] = useState(12);
  const [referral, setReferral] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    const file = inputRef.current?.files?.[0];
    if (!file) {
      setError("Выбери видеофайл");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("account_handle", handle);
      form.append("platform", "TikTok");
      form.append("account_age_days", String(ageDays));
      form.append("follower_growth", String(growth));
      form.append("referral_link_in_bio", String(referral));
      await analyzeVideo(form);
      router.refresh();
      if (inputRef.current) inputRef.current.value = "";
    } catch {
      setError("Анализ не удался — проверь, что бэкенд запущен (uvicorn api.main:app)");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border border-dashed border-border-strong bg-bg-surface-2 p-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-[11px] text-text-muted">Видео</label>
          <input ref={inputRef} type="file" accept="video/*" className="text-xs text-text-primary" />
        </div>
        <div>
          <label className="block text-[11px] text-text-muted">@handle</label>
          <input
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            className="w-32 rounded border border-border-subtle bg-bg-surface-1 px-2 py-1 text-xs"
          />
        </div>
        <div>
          <label className="block text-[11px] text-text-muted">Возраст аккаунта (дни)</label>
          <input
            type="number"
            value={ageDays}
            onChange={(e) => setAgeDays(Number(e.target.value))}
            className="w-24 rounded border border-border-subtle bg-bg-surface-1 px-2 py-1 text-xs"
          />
        </div>
        <div>
          <label className="block text-[11px] text-text-muted">Рост подписчиков (x/нед)</label>
          <input
            type="number"
            value={growth}
            onChange={(e) => setGrowth(Number(e.target.value))}
            className="w-24 rounded border border-border-subtle bg-bg-surface-1 px-2 py-1 text-xs"
          />
        </div>
        <label className="flex items-center gap-1.5 text-xs text-text-muted">
          <input type="checkbox" checked={referral} onChange={(e) => setReferral(e.target.checked)} />
          реф-ссылка в био
        </label>
        <button
          onClick={handleSubmit}
          disabled={busy}
          className="flex items-center gap-1.5 rounded-md bg-brand-500 px-3 py-1.5 text-xs font-semibold text-bg-base hover:bg-brand-400 disabled:opacity-50"
        >
          <Upload className="size-3.5" /> {busy ? "Анализирую..." : "Прогнать через pipeline"}
        </button>
      </div>
      {error && <div className="mt-2 text-xs text-sev-high">{error}</div>}
    </div>
  );
}
