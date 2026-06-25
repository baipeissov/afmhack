"""
Базовый спец-агент: общий каркас для экспертов по типам мошенничества.

Каждый специалист = (а) детерминированные правила под свой класс
(ключевые слова/regex/визуальные CLIP-маркеры), (б) LLM-эксперт с узким
системным промптом, выдающий структурированный вердикт. Результат пишется
в поле case["specialist"] и может скорректировать risk_score.

LLM опционален: если OPENROUTER_API_KEY не задан или модели недоступны,
специалист всё равно отдаёт rule-based вердикт (graceful degradation).
"""

from __future__ import annotations

import logging
import re

from ..base import Agent
from ..llm import LLMError, default_client

log = logging.getLogger("sunkar.specialists")

PERCENT_RE = re.compile(r"\d+[.,]?\d*\s*%")


def case_text_blob(case: dict) -> str:
    """Собирает весь текстовый сигнал кейса: подпись + транскрипт + OCR."""
    parts: list[str] = []
    if case.get("caption"):
        parts.append(str(case["caption"]))
    raw = case.get("raw") or {}
    for seg in raw.get("transcript", []):
        if seg.get("text"):
            parts.append(seg["text"])
    for seg in raw.get("ocr", []):
        if seg.get("text"):
            parts.append(seg["text"])
    return "\n".join(parts)


def visual_markers(case: dict) -> dict[str, float]:
    """Максимум по каждому визуальному маркеру (CLIP) за все кадры."""
    raw = case.get("raw") or {}
    out: dict[str, float] = {}
    for frame in raw.get("visual", []):
        for marker, score in (frame.get("scores") or {}).items():
            out[marker] = max(out.get(marker, 0.0), float(score))
    return out


class BaseSpecialist(Agent):
    # переопределяются в подклассах
    violation_class: str = "clean"
    display_ru: str = ""
    keywords: list[str] = []
    visual_markers_of_interest: list[str] = []
    expert_focus: str = ""  # вставляется в системный промпт

    @property
    def name(self) -> str:  # type: ignore[override]
        return f"specialist_{self.violation_class}"

    # ── детерминированные правила ──
    def rule_signals(self, case: dict) -> dict:
        text = case_text_blob(case).lower()
        hits = sorted({k for k in self.keywords if k.lower() in text})
        percents = PERCENT_RE.findall(text)
        vmarks = visual_markers(case)
        vhits = {m: round(vmarks[m], 3) for m in self.visual_markers_of_interest if vmarks.get(m, 0) > 0.26}
        score = min(0.4, 0.06 * len(hits)) + (0.1 if percents else 0.0) + min(0.2, 0.1 * len(vhits))
        return {
            "keyword_hits": hits,
            "percent_mentions": percents[:5],
            "visual_hits": vhits,
            "rule_score": round(min(score, 0.6), 3),
        }

    # ── LLM-эксперт ──
    def llm_verdict(self, case: dict, signals: dict) -> dict:
        if not default_client.available:
            return {"available": False}
        text = case_text_blob(case)[:3000] or "(нет распознанного текста)"
        vhits = signals.get("visual_hits") or {}
        system = (
            "Ты — эксперт Агентства по финансовому мониторингу РК по выявлению "
            f"схемы типа «{self.display_ru}». {self.expert_focus} "
            "Анализируй ТОЛЬКО предоставленные сигналы из публичного видео "
            "(транскрипт/субтитры/подпись/визуальные маркеры). Не выдумывай фактов. "
            "Ответь СТРОГО в JSON со схемой: "
            '{"confirmed": bool, "confidence": число 0..1, '
            '"indicators": [строки], "quotes": [короткие цитаты-улики], '
            '"rationale": "1-2 предложения по-русски"}.'
        )
        user = (
            f"Класс для проверки: {self.display_ru}\n"
            f"Визуальные маркеры (CLIP): {vhits}\n"
            f"Ключевые слова сработали: {signals.get('keyword_hits')}\n\n"
            f"ТЕКСТ ВИДЕО:\n{text}"
        )
        try:
            data = default_client.chat_json(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.2, max_tokens=500,
            )
            data["available"] = True
            return data
        except LLMError as e:
            log.warning("LLM verdict недоступен (%s): %s", self.violation_class, e)
            return {"available": False, "error": str(e)}

    # ── публичный разбор ──
    def analyze(self, case: dict) -> dict:
        signals = self.rule_signals(case)
        verdict = self.llm_verdict(case, signals)

        confirmed = bool(verdict.get("confirmed")) if verdict.get("available") else (signals["rule_score"] >= 0.2)
        confidence = float(verdict.get("confidence", signals["rule_score"])) if verdict.get("available") else signals["rule_score"]

        # корректировка риска: подтверждение экспертом усиливает, опровержение ослабляет
        risk_adjust = 0.0
        if verdict.get("available"):
            risk_adjust = round((confidence - 0.5) * 0.2, 3)  # ±0.1
        else:
            risk_adjust = round(min(0.1, signals["rule_score"] * 0.2), 3)

        result = {
            "specialist": self.violation_class,
            "display_ru": self.display_ru,
            "confirmed": confirmed,
            "confidence": round(confidence, 3),
            "rule_signals": signals,
            "indicators": verdict.get("indicators", signals["keyword_hits"]),
            "quotes": verdict.get("quotes", []),
            "rationale": verdict.get("rationale", "Вердикт по детерминированным правилам (LLM недоступен)."),
            "llm_used": bool(verdict.get("available")),
            "risk_adjust": risk_adjust,
        }
        self.log_action("analyzed", item_id=case.get("item_id"), confirmed=confirmed,
                        confidence=result["confidence"], llm=result["llm_used"])
        return result
