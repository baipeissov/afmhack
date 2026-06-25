"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { fetchQueue, type QueueRecord } from "@/lib/api";
import { downloadReport, liaisonChat } from "@/lib/agents";

type Msg = { role: "user" | "assistant"; content: string };

export default function LiaisonPage() {
  const [cases, setCases] = useState<QueueRecord[]>([]);
  const [caseId, setCaseId] = useState<string>("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchQueue().then((q) => {
      setCases(q);
      if (q.length) setCaseId(q[0].item_id);
    });
  }, []);

  useEffect(() => {
    setMessages([]);
  }, [caseId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const q = input.trim();
    if (!q || !caseId || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setBusy(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await liaisonChat(caseId, q, history);
      setMessages((m) => [...m, { role: "assistant", content: res.answer }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "⚠ Бэкенд недоступен (запустите api.main на :8000)." }]);
    } finally {
      setBusy(false);
    }
  }

  async function report() {
    if (!caseId) return;
    try {
      const url = await downloadReport(caseId, "Аналитик АФМ");
      window.open(url, "_blank");
      toast.success("Рапорт DOCX сформирован");
    } catch {
      toast.error("Не удалось сформировать рапорт");
    }
  }

  const selected = cases.find((c) => c.item_id === caseId);

  return (
    <div className="flex h-full flex-col p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-text-primary">Связной с АФМ</h1>
          <p className="mt-0.5 text-sm text-text-secondary">
            Спросите по кейсу — агент ответит по собранным доказательствам и сформирует рапорт.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
            className="rounded-lg border border-border-strong bg-bg-surface-1 px-2 py-1.5 text-sm text-text-primary"
          >
            {cases.length === 0 && <option value="">нет кейсов</option>}
            {cases.map((c) => (
              <option key={c.item_id} value={c.item_id}>
                @{c.account_handle} · {c.top_class_ru} · {(c.risk_score * 100).toFixed(0)}%
              </option>
            ))}
          </select>
          <button
            onClick={report}
            disabled={!caseId}
            className="rounded-lg bg-brand-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50"
          >
            ⤓ Рапорт DOCX
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-border-subtle bg-bg-base">
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="mt-10 text-center text-sm text-text-muted">
              {selected ? (
                <>Задайте вопрос по кейсу <span className="font-mono">@{selected.account_handle}</span> —
                  например: «Почему высокий риск?», «Какие доказательства?», «Что рекомендуете?»</>
              ) : (
                "Нет кейсов в очереди. Запустите бэкенд и discovery."
              )}
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm ${
                  m.role === "user"
                    ? "bg-brand-500 text-white"
                    : "border border-border-subtle bg-bg-surface-1 text-text-primary"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {busy && <div className="text-xs text-text-muted">Агент печатает…</div>}
          <div ref={endRef} />
        </div>

        <div className="flex items-center gap-2 border-t border-border-subtle bg-bg-surface-1 p-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Спросите по кейсу…"
            disabled={!caseId || busy}
            className="flex-1 rounded-lg border border-border-strong bg-bg-base px-3 py-2 text-sm text-text-primary outline-none focus:border-brand-500"
          />
          <button
            onClick={send}
            disabled={!caseId || busy || !input.trim()}
            className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50"
          >
            Отправить
          </button>
        </div>
      </div>
    </div>
  );
}
