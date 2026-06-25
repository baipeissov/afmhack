"""
LiaisonAgent — связной с сотрудниками АФМ.

Отвечает на вопросы по кейсу на естественном языке, опираясь СТРОГО на
собранные данные (досье, вердикт специалиста, граф связей, переписка
следователя), и по запросу генерит официальный DOCX-рапорт (переиспользуя
backend/report_generator.py).

Тон — аккуратный, со ссылками на доказательства с таймкодами. Не выдумывает
фактов: если данных нет, прямо об этом говорит.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ..base import DATA_DIR, Agent, get_case
from ..llm import LLMError, default_client

log = logging.getLogger("sunkar.liaison")

ENGAGEMENT_DIR = DATA_DIR / "engagement"


def _engagement(case_id: str) -> dict | None:
    p = ENGAGEMENT_DIR / f"{case_id.replace('/', '_')}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def build_case_context(case_id: str) -> dict | None:
    """Собирает всё, что известно по кейсу, для grounding ответа."""
    case = get_case(case_id)
    if case is None:
        return None
    convo = _engagement(case_id)
    return {
        "case_id": case_id,
        "account": case.get("account_handle"),
        "platform": case.get("platform"),
        "risk_score": case.get("risk_score"),
        "risk_level": case.get("risk_level"),
        "top_class_ru": case.get("top_class_ru"),
        "explanations": case.get("explanations", []),
        "recommendation": case.get("recommendation"),
        "specialist": case.get("specialist"),
        "network_connections": case.get("network_connections"),
        "probe_result": case.get("probe_result"),
        "engagement_intelligence": (convo or {}).get("intelligence"),
        "engagement_messages": len((convo or {}).get("messages", [])),
        "status": case.get("status"),
    }


def _context_text(ctx: dict) -> str:
    return json.dumps(ctx, ensure_ascii=False, indent=2)


def _render_context(ctx: dict) -> str:
    """Человекочитаемая сводка кейса — надёжнее для слабых моделей, чем сырой JSON."""
    lines = [
        f"Кейс: {ctx.get('case_id')}",
        f"Аккаунт: @{ctx.get('account')} ({ctx.get('platform')})",
        f"Класс нарушения: {ctx.get('top_class_ru')}",
        f"Risk score: {ctx.get('risk_score')} (уровень {ctx.get('risk_level')})",
        f"Рекомендация системы: {ctx.get('recommendation')}",
        f"Статус: {ctx.get('status')}",
    ]
    if ctx.get("explanations"):
        lines.append("Доказательства:")
        lines += [f"  - {e}" for e in ctx["explanations"][:10]]
    sp = ctx.get("specialist") or {}
    if sp:
        lines.append(f"Вердикт спец-агента: подтверждено={sp.get('confirmed')}, "
                     f"уверенность={sp.get('confidence')} — {sp.get('rationale','')}")
    if ctx.get("network_connections"):
        lines.append(f"Связей в графе: {len(ctx['network_connections'])}")
    intel = ctx.get("engagement_intelligence") or {}
    if intel:
        lines.append(f"Из переписки следователя: {intel.get('summary','')}")
        if intel.get("payment_details"):
            lines.append(f"  Реквизиты: {intel.get('payment_details')}")
    return "\n".join(lines)


class LiaisonAgent(Agent):
    name = "liaison"

    def chat(self, case_id: str, question: str, history: list[dict] | None = None) -> dict:
        ctx = build_case_context(case_id)
        if ctx is None:
            return {"ok": False, "reason": "case_not_found"}
        if not default_client.available:
            return {"ok": True, "answer": "LLM недоступен. Сводка по кейсу:\n" + _context_text(ctx),
                    "llm_used": False}

        system = (
            "Ты — ассистент-связной Агентства по финансовому мониторингу РК. "
            "Тебе ВСЕГДА предоставляются полные данные по кейсу ниже в сообщении "
            "пользователя — они достаточны для ответа, считай их фактами и отвечай по ним. "
            "Тон деловой, по-русски, кратко, со ссылками на доказательства (таймкоды/цитаты). "
            "Не проси дополнительных данных — всё необходимое уже дано."
        )
        messages = [{"role": "system", "content": system}]
        for h in (history or [])[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({
            "role": "user",
            "content": f"ДАННЫЕ ПО КЕЙСУ:\n{_render_context(ctx)}\n\nВОПРОС СОТРУДНИКА: {question}",
        })
        try:
            resp = default_client.chat(messages, temperature=0.3, max_tokens=700)
            self.log_action("chat", item_id=case_id)
            return {"ok": True, "answer": resp.text, "llm_used": True, "model": resp.model}
        except LLMError as e:
            return {"ok": True, "answer": f"Не удалось получить ответ модели: {e}", "llm_used": False}

    # ── официальный рапорт DOCX ──
    def _case_for_report(self, case: dict, analyst: str) -> dict:
        convo = _engagement(case["item_id"]) or {}
        evidence = []
        for expl in case.get("explanations", []):
            evidence.append({"timestamp": "", "type": "signal", "description": expl, "confidence": None})
        return {
            "case_id": case["item_id"],
            "created_at": datetime.now(timezone.utc),
            "analyst_name": analyst,
            "account": {
                "handle": case.get("account_handle", "unknown"),
                "platform": case.get("platform", ""),
                "url": case.get("url", ""),
                "bio": case.get("caption", ""),
            },
            "risk_score": case.get("risk_score", 0.0),
            "violation_class": case.get("top_class", "clean"),
            "evidence": evidence,
            "probe_result": case.get("probe_result"),
            "network_connections": case.get("network_connections"),
            "engagement_intelligence": convo.get("intelligence"),
        }

    def generate_report(self, case_id: str, analyst: str, out_dir: Path | None = None) -> dict:
        case = get_case(case_id)
        if case is None:
            return {"ok": False, "reason": "case_not_found"}
        try:
            from backend.report_generator import AFMReportGenerator  # ленивый импорт (python-docx)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": f"report_generator_unavailable: {e}"}

        data = AFMReportGenerator().generate(self._case_for_report(case, analyst))
        out_dir = Path(out_dir or (DATA_DIR / "reports"))
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"AFM_report_{case_id}.docx"
        path.write_bytes(data)
        self.log_action("report_generated", item_id=case_id, path=str(path), bytes=len(data))
        return {"ok": True, "path": str(path), "bytes": len(data)}
