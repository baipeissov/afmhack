"""
AnalysisAgent — обёртка над реальным пайплайном (api/dossier.build_dossier:
audio→ocr→visual→Component A→Component B). Превращает DiscoveredItem в запись
risk-очереди той же формы, что пишет api/main.py, и дозаписывает в общий
data/risk_queue.jsonl.

build_dossier импортируется ЛЕНИВО (внутри функции), потому что он тянет
тяжёлый ML-стек (torch/whisper/paddle/clip). Это позволяет грузить агентный
слой и его лёгкие эндпоинты на машине без полного ML-стека.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from pipeline.connectors.base import DiscoveredItem

from .base import RISK_QUEUE, Agent, append_jsonl

log = logging.getLogger("sunkar.agents.analysis")


def dossier_to_queue_record(dossier: dict, item: DiscoveredItem, platform: str) -> dict:
    """Та же схема, что api/main._dossier_to_queue_record — фронт ждёт именно её."""
    raw = dossier["raw"]
    return {
        "item_id": item.item_id,
        "source": item.source,
        "account_handle": item.account_handle or "unknown",
        "platform": platform,
        "video_path": dossier["video_path"],
        "risk_score": dossier["risk_score"],
        "risk_level": dossier["risk_level"],
        "top_class": dossier["top_class"],
        "top_class_ru": dossier["top_class_ru"],
        "contributions": dossier["contributions"],
        "explanations": dossier["explanations"],
        "recommendation": dossier["recommendation"],
        "modalities": {
            "asr": len(raw["transcript"]) > 0,
            "ocr": len(raw["ocr"]) > 0,
            "vision": len(raw["visual"]) > 0,
        },
        "caption": item.caption or "",
        "url": item.url,
        "discovered_at": item.discovered_at or datetime.now(timezone.utc).isoformat(),
        "status": "pending_review",
        "analyst_comment": None,
        "raw": raw,  # держим raw для спец-агентов и dataset-куратора
    }


def _platform_of(item: DiscoveredItem) -> str:
    src = (item.source or "").lower()
    if "instagram" in src:
        return "Instagram"
    if "tiktok" in src:
        return "TikTok"
    return item.metadata.get("platform", "TikTok") if item.metadata else "TikTok"


class AnalysisAgent(Agent):
    name = "analysis"

    def analyze_item(self, item: DiscoveredItem, account_metadata: dict | None = None) -> dict | None:
        """Гоняет видео через пайплайн, пишет запись в risk_queue, возвращает её."""
        if not item.local_path:
            log.warning("у %s нет local_path — нечего анализировать", item.item_id)
            return None
        try:
            from api.dossier import build_dossier  # ленивый импорт тяжёлого стека
        except Exception as e:  # noqa: BLE001
            log.error("ML-стек недоступен (build_dossier): %s", e)
            self.log_action("ml_unavailable", item_id=item.item_id, error=str(e))
            return None

        dossier = build_dossier(item.local_path, account_metadata)
        record = dossier_to_queue_record(dossier, item, _platform_of(item))
        append_jsonl(RISK_QUEUE, record)
        self.log_action("analyzed", item_id=item.item_id, risk=record["risk_score"],
                        top_class=record["top_class"])
        return record
