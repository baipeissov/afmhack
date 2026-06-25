"""
Маленькая локальная LLM (Llama 3.2 3B через Ollama) разбирает конкретный
сегмент транскрипта/OCR, который Component A уже пометил как fraud-класс,
и объясняет human-readable фразой, что именно здесь нарушение — вместо
того чтобы аналитик читал только название класса и число p=0.58.

Намеренно НЕ прогоняем LLM по всему видео — только по уже отфильтрованным
evidence-сегментам (Component A решает ЧТО подозрительно, LLM решает КАК
это объяснить). Так дешевле и предсказуемее по времени на демо.

Надёжность для сцены: если Ollama не запущен/не отвечает, тихо откатываемся
на None — вызывающий код (api/dossier.py) показывает свои шаблонные
объяснения как и раньше. Демо не должно падать из-за LLM.
"""

import logging

import requests

logger = logging.getLogger("llm_explainer")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"
TIMEOUT_SECONDS = 30  # первый запрос после холодного старта Ollama грузит модель в память — это дольше, чем обычный inference
MAX_RESPONSE_TOKENS = 60  # короткое объяснение, не абзац — для отчёта аналитику

PROMPT_TEMPLATE = (
    "Ты помогаешь финансовому аналитику АФМ. Вот фраза из видео "
    '(таймкод {timecode}): "{text}"\n'
    "Классификатор пометил это как: {class_ru}.\n"
    "Объясни ОДНИМ коротким предложением на русском, что именно в этой "
    "фразе является признаком нарушения. Без вступлений, сразу суть."
)


def _is_available() -> bool:
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except requests.RequestException:
        return False


def explain_segment(text: str, class_ru: str, timecode: str) -> str | None:
    """Возвращает короткое объяснение или None, если LLM недоступна/упала —
    вызывающий код должен в этом случае использовать шаблонное объяснение."""
    prompt = PROMPT_TEMPLATE.format(timecode=timecode, text=text, class_ru=class_ru)
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": MAX_RESPONSE_TOKENS, "temperature": 0.2},
            },
            timeout=TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        explanation = resp.json().get("response", "").strip()
        return explanation or None
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.warning("LLM explain failed, falling back to template: %s", e)
        return None


def explain_evidence(evidence: list[dict], max_items: int = 3) -> list[dict]:
    """evidence: список {row, class, prob, ...} как в api/dossier.py
    (transcript_evidence/ocr_evidence). Объясняет только первые max_items —
    топ по уверенности — чтобы не ждать LLM по каждому сегменту."""
    if not evidence or not _is_available():
        return []

    results = []
    for e in evidence[:max_items]:
        row = e["row"]
        t = row.get("start", row.get("frame_time", 0))
        timecode = f"{int(t // 60):02d}:{int(t % 60):02d}"
        explanation = explain_segment(row["text"], e["class_ru"], timecode)
        if explanation:
            results.append({"timecode": timecode, "text": row["text"], "llm_explanation": explanation})
    return results


if __name__ == "__main__":
    print(explain_segment(
        "Пятьдесят процентов прибыли за 45 дней.",
        "гарантированный доход / пирамида",
        "00:11",
    ))
