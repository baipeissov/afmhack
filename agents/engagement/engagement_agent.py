"""
EngagementAgent — следователь под контролем человека.

Жизненный цикл переписки по кейсу:
  start()            → строит легенду, ГОТОВИТ первое сообщение (draft), не шлёт.
  approve_and_send() → аналитик подтверждает draft → отправка (по умолчанию
                       симуляция) → получаем ответ «мошенника» → в историю.
  draft_next()       → готовит следующее сообщение (draft) на основе истории.
  reject_draft()     → отклонить подготовленное сообщение.
  summarize()        → LLM сводит добытые улики (реквизиты, механика, админ).

Инвариант: ни одно исходящее сообщение не уходит без approve_and_send().
Всё пишется в data/engagement_log.jsonl.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ..base import DATA_DIR, Agent, append_jsonl, get_case
from ..llm import LLMError, default_client
from .persona import build_persona
from .transports import get_transport

log = logging.getLogger("sunkar.engagement.agent")

ENGAGEMENT_DIR = DATA_DIR / "engagement"
ENGAGEMENT_LOG = DATA_DIR / "engagement_log.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _convo_path(case_id: str) -> Path:
    ENGAGEMENT_DIR.mkdir(parents=True, exist_ok=True)
    safe = case_id.replace("/", "_")
    return ENGAGEMENT_DIR / f"{safe}.json"


class EngagementAgent(Agent):
    name = "engagement"

    # ── хранилище переписки ──
    def _load(self, case_id: str) -> dict | None:
        p = _convo_path(case_id)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def _save(self, convo: dict) -> None:
        _convo_path(convo["case_id"]).write_text(
            json.dumps(convo, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _audit(self, event: str, **fields) -> None:
        append_jsonl(ENGAGEMENT_LOG, {"ts": _now(), "event": event, **fields})

    # ── шаги ──
    def start(self, case_id: str) -> dict:
        case = get_case(case_id)
        if case is None:
            return {"ok": False, "reason": "case_not_found"}
        if self._load(case_id):
            return {"ok": False, "reason": "already_started"}

        persona = build_persona(case)
        convo = {
            "case_id": case_id,
            "scheme": persona.get("scheme"),
            "persona": persona,
            "transport": get_transport(case).name,
            "status": "active",
            "messages": [],
            "pending_draft": {"text": persona.get("opening_hook", "Здравствуйте! Расскажите подробнее?"),
                              "ts": _now(), "kind": "opening"},
            "intelligence": None,
        }
        self._save(convo)
        self._audit("started", case_id=case_id, transport=convo["transport"], persona=persona.get("name"))
        self.log_action("started", item_id=case_id)
        return {"ok": True, "convo": convo}

    def _draft_message(self, convo: dict) -> str:
        persona = convo.get("persona", {})
        if not default_client.available:
            return "Понятно. А можно подробнее: куда переводить и какие гарантии?"
        system = (
            "Ты — оперативник АФМ под легендой потенциальной жертвы в санкционированной "
            "проверке. Твоя задача — естественной перепиской выманить у мошенника: механику "
            "схемы, платёжные реквизиты/кошелёк, личность администратора, обещания дохода. "
            f"Легенда: {persona.get('legend','')}. Цели: {persona.get('goals')}. "
            "Сгенерируй ТОЛЬКО следующее короткое сообщение от твоего лица (по-русски), "
            "не раскрывая, что ты из органов. Без кавычек и пояснений."
        )
        convo_msgs = [{"role": "system", "content": system}]
        for m in convo.get("messages", []):
            role = "user" if m.get("from") == "fraudster" else "assistant"
            convo_msgs.append({"role": role, "content": m.get("text", "")})
        convo_msgs.append({"role": "user", "content": "Сформулируй следующее сообщение."})
        try:
            return default_client.chat(convo_msgs, temperature=0.7, max_tokens=200).text.strip()
        except LLMError as e:
            log.warning("draft LLM error: %s", e)
            return "А какие гарантии возврата и куда именно переводить?"

    def draft_next(self, case_id: str) -> dict:
        convo = self._load(case_id)
        if convo is None:
            return {"ok": False, "reason": "not_started"}
        if convo.get("pending_draft"):
            return {"ok": False, "reason": "draft_already_pending", "pending": convo["pending_draft"]}
        text = self._draft_message(convo)
        convo["pending_draft"] = {"text": text, "ts": _now(), "kind": "reply"}
        self._save(convo)
        self._audit("drafted", case_id=case_id, text=text)
        return {"ok": True, "pending_draft": convo["pending_draft"]}

    def approve_and_send(self, case_id: str, analyst: str, edited_text: str | None = None) -> dict:
        """Аналитик подтверждает (опц. редактирует) draft → отправка → ответ."""
        convo = self._load(case_id)
        if convo is None:
            return {"ok": False, "reason": "not_started"}
        draft = convo.get("pending_draft")
        if not draft:
            return {"ok": False, "reason": "no_pending_draft"}

        text = (edited_text or draft["text"]).strip()
        case = get_case(case_id) or {}
        transport = get_transport(case)

        # исходящее (подтверждённое человеком)
        convo["messages"].append({
            "from": "investigator", "text": text, "status": "sent",
            "approved_by": analyst, "ts": _now(),
        })
        self._audit("approved_sent", case_id=case_id, analyst=analyst, text=text, transport=transport.name)

        # ответ собеседника (в симуляции — LLM-«мошенник»; в live-каналах прилетит отдельно)
        try:
            result = transport.send(case, convo["messages"], text)
        except Exception as e:  # noqa: BLE001 — например EngagementBlocked
            convo["pending_draft"] = None
            self._save(convo)
            self._audit("send_blocked", case_id=case_id, error=str(e), transport=transport.name)
            return {"ok": True, "sent": True, "reply": None, "note": f"Отправлено, ответ не получен: {e}"}

        reply = result.get("reply")
        if reply:
            convo["messages"].append({
                "from": "fraudster", "text": reply, "status": "received",
                "channel": result.get("channel"), "simulated": result.get("simulated", False), "ts": _now(),
            })
            self._audit("reply_received", case_id=case_id, channel=result.get("channel"),
                        simulated=result.get("simulated", False))
        convo["pending_draft"] = None
        self._save(convo)
        self.log_action("turn", item_id=case_id, analyst=analyst)
        return {"ok": True, "sent": True, "reply": reply, "simulated": result.get("simulated", False)}

    def reject_draft(self, case_id: str, analyst: str) -> dict:
        convo = self._load(case_id)
        if convo is None or not convo.get("pending_draft"):
            return {"ok": False, "reason": "no_pending_draft"}
        rejected = convo["pending_draft"]
        convo["pending_draft"] = None
        self._save(convo)
        self._audit("draft_rejected", case_id=case_id, analyst=analyst, text=rejected.get("text"))
        return {"ok": True}

    def conversation(self, case_id: str) -> dict | None:
        return self._load(case_id)

    def summarize(self, case_id: str) -> dict:
        """LLM сводит добытые улики для рапорта."""
        convo = self._load(case_id)
        if convo is None:
            return {"ok": False, "reason": "not_started"}
        transcript = "\n".join(f"{m['from']}: {m['text']}" for m in convo.get("messages", []))
        if not transcript:
            return {"ok": False, "reason": "empty_conversation"}
        if not default_client.available:
            convo["intelligence"] = {"summary": "LLM недоступен — сведение вручную", "transcript": transcript}
            self._save(convo)
            return {"ok": True, "intelligence": convo["intelligence"]}
        system = (
            "Ты — аналитик АФМ. По переписке оперативника с мошенником извлеки улики. "
            "Ответь СТРОГО JSON: {\"scheme_mechanics\": str, \"payment_details\": [str], "
            "\"contacts\": [str], \"admin_identity\": str, \"income_promises\": [str], "
            "\"summary\": str (2-3 предложения по-русски)}."
        )
        try:
            intel = default_client.chat_json(
                [{"role": "system", "content": system},
                 {"role": "user", "content": transcript[:4000]}],
                temperature=0.2, max_tokens=600,
            )
        except LLMError as e:
            intel = {"summary": f"Не удалось свести (LLM): {e}", "transcript": transcript}
        convo["intelligence"] = intel
        self._save(convo)
        self._audit("summarized", case_id=case_id)
        return {"ok": True, "intelligence": intel}
