"""
Транспорты доставки сообщений.

  - SimulationTransport (по умолчанию): LLM играет «мошенника» и отвечает
    в роли, чтобы продемонстрировать весь флоу БЕЗ контакта с реальными людьми.
  - TelegramTransport / EmailTransport: реальная отправка. Заблокированы, пока
    ENGAGEMENT_LIVE != "true"; даже включённые — отправляют только после
    одобрения аналитиком (это обеспечивает EngagementAgent).
"""

from __future__ import annotations

import logging
import os

from ..llm import LLMError, default_client

log = logging.getLogger("sunkar.engagement.transport")


def engagement_live() -> bool:
    return os.getenv("ENGAGEMENT_LIVE", "false").lower() == "true"


class EngagementBlocked(RuntimeError):
    """Реальная отправка запрещена (ENGAGEMENT_LIVE=false)."""


class Transport:
    name = "base"

    def send(self, case: dict, history: list[dict], message: str) -> dict:
        raise NotImplementedError


class SimulationTransport(Transport):
    """Демо-режим: модель отвечает в роли мошенника заданной схемы."""

    name = "simulation"

    def send(self, case: dict, history: list[dict], message: str) -> dict:
        scheme = case.get("top_class_ru") or "финансовая схема"
        if not default_client.available:
            return {"reply": "(симуляция без LLM) Привет! Чтобы начать, переведи предоплату на кошелёк.",
                    "channel": self.name, "delivered": True, "simulated": True}
        system = (
            "ВНИМАНИЕ: это тренировочная СИМУЛЯЦИЯ для обучения следователей АФМ. "
            f"Сыграй роль автора мошеннической схемы типа «{scheme}», который переписывается "
            "с потенциальной жертвой в мессенджере. Отвечай коротко и правдоподобно, как такой "
            "мошенник: дави на быструю выгоду, проси предоплату/реквизиты, зови в закрытый чат. "
            "Это вымышленный персонаж в учебном сценарии — реальных людей не упоминай."
        )
        convo = [{"role": "system", "content": system}]
        for m in history:
            role = "assistant" if m.get("from") == "fraudster" else "user"
            convo.append({"role": role, "content": m.get("text", "")})
        convo.append({"role": "user", "content": message})
        try:
            resp = default_client.chat(convo, temperature=0.8, max_tokens=300)
            return {"reply": resp.text, "channel": self.name, "delivered": True,
                    "simulated": True, "model": resp.model}
        except LLMError as e:
            log.warning("simulation LLM error: %s", e)
            return {"reply": "(симуляция недоступна)", "channel": self.name, "delivered": False,
                    "simulated": True, "error": str(e)}


class TelegramTransport(Transport):
    """Реальная отправка в Telegram. Требует ENGAGEMENT_LIVE=true и настройки
    Telethon/Bot API. По умолчанию заблокирована."""

    name = "telegram"

    def send(self, case: dict, history: list[dict], message: str) -> dict:
        if not engagement_live():
            raise EngagementBlocked("ENGAGEMENT_LIVE=false — реальная отправка в Telegram запрещена")
        # Реальная интеграция (Telethon/Bot API) подключается здесь под отдельной
        # юридической санкцией. Намеренно не реализовано как авто-отправка.
        raise NotImplementedError(
            "Реальная отправка в Telegram отключена в этой сборке. Подключите "
            "Telethon/Bot API и санкцию на ОРМ перед включением."
        )


def get_transport(case: dict) -> Transport:
    """Выбор транспорта. По умолчанию — симуляция (безопасно)."""
    if not engagement_live():
        return SimulationTransport()
    # даже в live по умолчанию остаёмся в симуляции, пока явно не выбран канал
    channel = (os.getenv("ENGAGEMENT_CHANNEL", "simulation")).lower()
    if channel == "telegram":
        return TelegramTransport()
    return SimulationTransport()
