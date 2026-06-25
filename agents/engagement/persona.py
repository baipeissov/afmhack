"""
Построение «легенды» (undercover persona) и плана диалога для расследования.

Агент действует от лица потенциальной жертвы, чтобы под санкцией аналитика
АФМ собрать доказательства схемы. Легенда — служебный инструмент расследования,
не для обмана непричастных людей.
"""

from __future__ import annotations

import logging

from ..llm import LLMError, default_client

log = logging.getLogger("sunkar.engagement.persona")

_FALLBACK = {
    "name": "Айдос",
    "legend": "33 года, Алматы, есть небольшие сбережения, ищет дополнительный доход, "
              "осторожен, но поддаётся на обещания быстрой прибыли.",
    "goals": [
        "узнать механику схемы (как именно «зарабатывают»)",
        "получить платёжные реквизиты / номер кошелька / карту",
        "выяснить, кто администратор и где сообщество (Telegram/закрытый чат)",
        "зафиксировать обещания гарантированного дохода",
    ],
    "opening_hook": "Здравствуйте! Увидел ваше видео, заинтересовало. Как начать и сколько нужно вложить?",
}


def build_persona(case: dict) -> dict:
    """LLM строит легенду под конкретный класс схемы. При недоступности LLM —
    разумный шаблон."""
    scheme = case.get("top_class_ru") or case.get("top_class") or "финансовое мошенничество"
    if not default_client.available:
        return {**_FALLBACK, "scheme": scheme, "llm_used": False}

    system = (
        "Ты помогаешь следователю Агентства по финансовому мониторингу РК спланировать "
        "санкционированную проверку: оперативник под легендой потенциальной жертвы выходит "
        "на контакт с автором мошеннической схемы, чтобы собрать доказательства. "
        "Сформируй легенду и цели. Ответь СТРОГО JSON: "
        '{"name": str, "legend": str, "goals": [str,...], "opening_hook": str (первое сообщение, '
        "естественное, по-русски, без раскрытия, что это проверка)}."
    )
    user = (
        f"Тип схемы: {scheme}\n"
        f"Подпись видео: {case.get('caption','')[:400]}\n"
        "Цель — выманить: механику схемы, платёжные реквизиты, личность администратора, "
        "обещания дохода."
    )
    try:
        data = default_client.chat_json(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.5, max_tokens=500,
        )
        data["scheme"] = scheme
        data["llm_used"] = True
        return data
    except LLMError as e:
        log.warning("persona LLM недоступен: %s", e)
        return {**_FALLBACK, "scheme": scheme, "llm_used": False}
