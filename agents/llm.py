"""
LLM-клиент через OpenRouter (OpenAI-совместимый API).

Используем ТОЛЬКО бесплатные модели с цепочкой фоллбэка — free-тиры часто
отдают 429/таймаут, поэтому при ошибке пробуем следующую модель в списке.
Ключ берётся из переменной окружения OPENROUTER_API_KEY (.env, не в git).

Зависимости: httpx (лёгкая, не тянет тяжёлый ML-стек). python-dotenv —
опционально, чтобы подхватить .env при локальном запуске.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass

import httpx

try:  # подхватываем .env, если установлен python-dotenv
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001
    pass

log = logging.getLogger("sunkar.llm")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Бесплатные модели OpenRouter (порядок = приоритет фоллбэка). Список может
# меняться на стороне OpenRouter; переопределяется через env SUNKAR_LLM_MODELS
# (через запятую).
DEFAULT_FREE_MODELS = [
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
]


def _models() -> list[str]:
    env = os.getenv("SUNKAR_LLM_MODELS")
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return DEFAULT_FREE_MODELS


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    text: str
    model: str
    raw: dict


class LLMClient:
    """Тонкий клиент OpenRouter с фоллбэком по бесплатным моделям."""

    def __init__(self, api_key: str | None = None, models: list[str] | None = None, timeout: float = 60.0):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.models = models or _models()
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter рекомендует указывать источник (необязательно).
            "HTTP-Referer": "https://afm.local/sunkar",
            "X-Title": "SUNKAR AFM Agent",
        }

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.4,
        max_tokens: int = 900,
        response_format: dict | None = None,
        retries_per_model: int = 1,
    ) -> LLMResponse:
        """Синхронный вызов чата. Пробует модели по очереди до первой удачной.

        messages — список {"role": "system"|"user"|"assistant", "content": str}.
        response_format={"type": "json_object"} просит модель вернуть JSON.
        """
        if not self.available:
            raise LLMError("OPENROUTER_API_KEY не задан (.env)")

        last_err: Exception | None = None
        for model in self.models:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                payload["response_format"] = response_format

            for attempt in range(retries_per_model + 1):
                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        r = client.post(OPENROUTER_URL, headers=self._headers(), json=payload)
                    if r.status_code == 429:
                        last_err = LLMError(f"{model}: rate limited (429)")
                        log.warning("LLM %s rate-limited, trying next model", model)
                        break  # к следующей модели
                    r.raise_for_status()
                    data = r.json()
                    choices = data.get("choices")
                    if not choices:
                        last_err = LLMError(f"{model}: ответ без choices: {str(data)[:160]}")
                        log.warning("LLM %s: нет choices, к следующей модели", model)
                        break
                    msg = choices[0].get("message", {}) or {}
                    # некоторые reasoning-модели кладут текст в reasoning, а content=None
                    text = msg.get("content") or msg.get("reasoning")
                    if not text:
                        last_err = LLMError(f"{model}: пустой content")
                        log.warning("LLM %s: пустой content, к следующей модели", model)
                        break
                    return LLMResponse(text=text, model=model, raw=data)
                except httpx.HTTPStatusError as e:
                    last_err = e
                    log.warning("LLM %s HTTP %s: %s", model, e.response.status_code, e.response.text[:200])
                    if e.response.status_code in (400, 404):
                        break  # модель недоступна — к следующей
                    time.sleep(1.0 * (attempt + 1))
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    log.warning("LLM %s error: %s", model, e)
                    time.sleep(1.0 * (attempt + 1))
        raise LLMError(f"Все модели недоступны. Последняя ошибка: {last_err}")

    def chat_json(self, messages: list[dict], **kwargs) -> dict:
        """Как chat(), но парсит ответ как JSON. Не навязываем response_format —
        не все бесплатные модели его поддерживают (часть отдаёт ошибку без
        choices). Полагаемся на инструкцию в промпте + устойчивый парсинг."""
        resp = self.chat(messages, **kwargs)
        return _extract_json(resp.text)


def _extract_json(text: str | None) -> dict:
    """Достаёт JSON из ответа модели, даже если он завёрнут в ```json ... ```."""
    if not text:
        raise LLMError("Пустой ответ модели (нет текста для JSON)")
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(f"Не удалось распарсить JSON из ответа модели: {e}\n{text[:300]}")


# Единый экземпляр для переиспользования агентами.
default_client = LLMClient()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    c = LLMClient()
    print("available:", c.available, "| models:", c.models[:2], "...")
    if c.available:
        resp = c.chat([
            {"role": "user", "content": "Ответь одним словом: работает?"},
        ])
        print(f"[{resp.model}] {resp.text!r}")
