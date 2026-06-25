"use client";

import { useRef, useState } from "react";
import { useRouter } from "@/i18n/navigation";
import { Link2, Upload } from "lucide-react";
import { analyzeUrl, analyzeVideo } from "@/lib/api";

/** Аналитик вставляет ссылку — caption/@handle вытягиваются сами через
 * yt-dlp на бэкенде (POST /analyze/url), без ручного ввода. Возраст
 * аккаунта/рост подписчиков платформы анонимно не отдают (нужен
 * TikTok Research API / Instagram Graph API с доступом), поэтому
 * оставлены опциональными — по умолчанию берутся нейтральные значения. */
function AnalyzeByUrl() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!url.trim()) {
      setError("Вставь ссылку на видео");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await analyzeUrl({ url: url.trim() });
      if (result.error) {
        setError(`Не удалось скачать видео по ссылке: ${result.detail ?? result.error}`);
        return;
      }
      setUrl("");
      router.refresh();
    } catch {
      setError("Анализ не удался — проверь, что бэкенд запущен (uvicorn api.main:app)");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="min-w-64 flex-1">
        <label className="block text-[11px] text-text-muted">Ссылка на видео (TikTok / Instagram)</label>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.tiktok.com/@.../video/..."
          className="w-full rounded border border-border-subtle bg-bg-surface-1 px-2 py-1.5 text-xs"
        />
      </div>
      <button
        onClick={handleSubmit}
        disabled={busy}
        className="flex items-center gap-1.5 rounded-md bg-brand-500 px-3 py-1.5 text-xs font-semibold text-bg-base hover:bg-brand-400 disabled:opacity-50"
      >
        <Link2 className="size-3.5" /> {busy ? "Скачиваю и анализирую..." : "Проанализировать по ссылке"}
      </button>
      {error && <div className="w-full text-xs text-sev-high">{error}</div>}
    </div>
  );
}

/** Запасной путь без URL — для теста на локальном файле, когда видео не
 * лежит публично на платформе. Метадату приходится вводить руками, потому
 * что без ссылки её не у кого спросить. */
function UploadFileFallback() {
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
        className="flex items-center gap-1.5 rounded-md bg-bg-surface-3 px-3 py-1.5 text-xs font-semibold text-text-primary hover:bg-bg-surface-2 disabled:opacity-50"
      >
        <Upload className="size-3.5" /> {busy ? "Анализирую..." : "Прогнать через pipeline"}
      </button>
      {error && <div className="mt-2 w-full text-xs text-sev-high">{error}</div>}
    </div>
  );
}

export function UploadTestVideo() {
  const [showFallback, setShowFallback] = useState(false);

  return (
    <div className="rounded-lg border border-dashed border-border-strong bg-bg-surface-2 p-4">
      <AnalyzeByUrl />
      <button
        onClick={() => setShowFallback((v) => !v)}
        className="mt-3 text-[11px] text-text-muted underline hover:text-text-secondary"
      >
        {showFallback ? "Скрыть" : "Нет ссылки? Загрузить файл вручную (тест без авто-метадаты)"}
      </button>
      {showFallback && (
        <div className="mt-3 border-t border-border-subtle pt-3">
          <UploadFileFallback />
        </div>
      )}
    </div>
  );
}
