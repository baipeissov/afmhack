"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { fetchQueue, type QueueRecord } from "@/lib/api";
import { engagement, type Conversation } from "@/lib/agents";

const ANALYST = "Аналитик АФМ";

export default function EngagementPage() {
  const [cases, setCases] = useState<QueueRecord[]>([]);
  const [caseId, setCaseId] = useState("");
  const [convo, setConvo] = useState<Conversation | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchQueue().then((q) => {
      // следователь — для рискованных кейсов (risk >= 0.7)
      const hot = q.filter((c) => c.risk_score >= 0.7);
      setCases(hot);
      if (hot.length) setCaseId(hot[0].item_id);
    });
  }, []);

  const load = useCallback(async (id: string) => {
    const c = await engagement.get(id);
    setConvo(c);
    setDraft(c?.pending_draft?.text ?? "");
  }, []);

  useEffect(() => {
    if (caseId) load(caseId);
  }, [caseId, load]);

  async function run(fn: () => Promise<unknown>, okMsg?: string) {
    setBusy(true);
    try {
      await fn();
      await load(caseId);
      if (okMsg) toast.success(okMsg);
    } catch {
      toast.error("Бэкенд недоступен (api.main на :8000)");
    } finally {
      setBusy(false);
    }
  }

  const start = () => run(() => engagement.start(caseId), "Расследование начато (симуляция)");
  const draftNext = () => run(() => engagement.draftNext(caseId));
  const approve = () => run(() => engagement.approve(caseId, ANALYST, draft), "Отправлено — получен ответ");
  const reject = () => run(() => engagement.reject(caseId, ANALYST), "Черновик отклонён");
  const summarize = () => run(() => engagement.summarize(caseId), "Улики сведены");

  const intel = convo?.intelligence as Record<string, unknown> | null | undefined;

  return (
    <div className="flex h-full flex-col p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-text-primary">Следователь (под контролем человека)</h1>
          <p className="mt-0.5 text-sm text-text-secondary">
            Агент готовит сообщения мошеннику — вы подтверждаете каждое. Режим симуляции (без реальной отправки).
          </p>
        </div>
        <select
          value={caseId}
          onChange={(e) => setCaseId(e.target.value)}
          className="rounded-lg border border-border-strong bg-bg-surface-1 px-2 py-1.5 text-sm text-text-primary"
        >
          {cases.length === 0 && <option value="">нет рискованных кейсов</option>}
          {cases.map((c) => (
            <option key={c.item_id} value={c.item_id}>
              @{c.account_handle} · {(c.risk_score * 100).toFixed(0)}%
            </option>
          ))}
        </select>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-3">
        {/* переписка */}
        <div className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-border-subtle bg-bg-base lg:col-span-2">
          <div className="flex items-center justify-between border-b border-border-subtle bg-bg-surface-1 px-3 py-2 text-xs text-text-muted">
            <span>Переписка {convo?.persona?.name ? `· легенда: ${convo.persona.name}` : ""}</span>
            <span className="rounded bg-bg-surface-3 px-2 py-0.5">{convo?.transport ?? "—"}</span>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {!convo && (
              <div className="mt-10 text-center text-sm text-text-muted">
                Расследование по кейсу не начато.
                <div className="mt-3">
                  <button onClick={start} disabled={!caseId || busy} className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50">
                    Начать расследование
                  </button>
                </div>
              </div>
            )}
            {convo?.messages.map((m, i) => (
              <div key={i} className={`flex ${m.from === "investigator" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm ${
                  m.from === "investigator" ? "bg-brand-500 text-white" : "border border-border-subtle bg-bg-surface-1 text-text-primary"
                }`}>
                  <div className="mb-0.5 text-[10px] opacity-70">
                    {m.from === "investigator" ? `следователь${m.approved_by ? ` · ✓ ${m.approved_by}` : ""}` : "мошенник (симуляция)"}
                  </div>
                  {m.text}
                </div>
              </div>
            ))}
          </div>

          {/* зона одобрения */}
          {convo && (
            <div className="border-t border-border-subtle bg-bg-surface-1 p-3">
              {convo.pending_draft ? (
                <>
                  <div className="mb-1 text-[10px] uppercase tracking-wide text-text-muted">
                    Черновик сообщения — требуется одобрение
                  </div>
                  <textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    rows={2}
                    className="w-full resize-y rounded-lg border border-border-strong bg-bg-base p-2 text-sm text-text-primary outline-none focus:border-brand-500"
                  />
                  <div className="mt-2 flex gap-2">
                    <button onClick={approve} disabled={busy} className="rounded-lg bg-brand-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50">
                      Одобрить и отправить
                    </button>
                    <button onClick={reject} disabled={busy} className="rounded-lg border border-border-strong px-3 py-1.5 text-sm text-text-primary hover:bg-bg-surface-2 disabled:opacity-50">
                      Отклонить
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex gap-2">
                  <button onClick={draftNext} disabled={busy} className="rounded-lg border border-border-strong px-3 py-1.5 text-sm text-text-primary hover:bg-bg-surface-2 disabled:opacity-50">
                    Подготовить ответ
                  </button>
                  <button onClick={summarize} disabled={busy} className="rounded-lg border border-border-strong px-3 py-1.5 text-sm text-text-primary hover:bg-bg-surface-2 disabled:opacity-50">
                    Свести улики
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* улики / легенда */}
        <div className="min-h-0 overflow-y-auto rounded-xl border border-border-subtle bg-bg-surface-1 p-4">
          <div className="text-[10px] font-semibold uppercase tracking-wide text-text-muted">Легенда</div>
          <div className="mt-1 text-sm text-text-secondary">{convo?.persona?.legend ?? "—"}</div>
          {convo?.persona?.goals && (
            <ul className="mt-2 list-disc pl-4 text-xs text-text-secondary">
              {convo.persona.goals.map((g, i) => <li key={i}>{g}</li>)}
            </ul>
          )}
          <div className="mt-4 text-[10px] font-semibold uppercase tracking-wide text-text-muted">Добытые улики</div>
          {intel ? (
            <pre className="mt-1 whitespace-pre-wrap break-words text-xs text-text-secondary">
              {String((intel as { summary?: string }).summary ?? JSON.stringify(intel, null, 2))}
            </pre>
          ) : (
            <div className="mt-1 text-xs text-text-muted">Нажмите «Свести улики» после переписки.</div>
          )}
        </div>
      </div>
    </div>
  );
}
