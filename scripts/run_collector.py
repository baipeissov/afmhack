"""
Collector — запускается один раз и работает непрерывно: по таймеру опрашивает
все зарегистрированные источники (pipeline/connectors/), и каждое новое
обнаруженное видео прогоняет через полный pipeline -> risk score -> очередь.

Запуск:
    python scripts/run_collector.py

Никакого ручного "вставь ссылку" на каждое видео — человек только
просматривает уже готовую risk-очередь и подтверждает/отклоняет (см. README,
human-in-the-loop).

Пока модули pipeline/* (Step 4) и fusion-модель (Step 5) не готовы,
process_item() — заглушка, которая просто кладёт айтем в очередь с
risk_score=None и source-инфой. Как только Component A/B обучены, сюда
подключится реальный анализ (см. TODO ниже).
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from api.dossier import build_dossier
from pipeline.connectors.tiktok_connector import TikTokHashtagConnector
from pipeline.connectors.instagram_connector import InstagramUrlListConnector
from pipeline.connectors.citizen_reports import CitizenReportsConnector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("collector")

POLL_INTERVAL_SECONDS = 15
QUEUE_PATH = Path(__file__).resolve().parents[1] / "data" / "risk_queue.jsonl"

CONNECTORS = [
    TikTokHashtagConnector(),
    InstagramUrlListConnector(),
    CitizenReportsConnector(),
]


def process_item(item) -> dict:
    """Полный анализ обнаруженного видео: pipeline (audio/ocr/visual/metadata)
    -> Component A -> Component B (fusion) -> запись очереди, готовая для
    дашборда (то же самое, что строит api/main.py:_dossier_to_queue_record)."""
    if not item.local_path:
        return {
            "item_id": item.item_id,
            "source": item.source,
            "status": "skipped_no_file",
            "risk_score": None,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }

    dossier = build_dossier(item.local_path, caption=item.caption)
    raw = dossier["raw"]
    return {
        "item_id": item.item_id,
        "source": item.source,
        "account_handle": item.account_handle or "unknown",
        "platform": "TikTok" if "tiktok" in item.source else "Instagram" if "instagram" in item.source else "TikTok",
        "video_path": dossier["video_path"],
        "risk_score": dossier["risk_score"],
        "risk_level": dossier["risk_level"],
        "top_class": dossier["top_class"],
        "top_class_ru": dossier["top_class_ru"],
        "contributions": dossier["contributions"],
        "explanations": dossier["explanations"],
        "recommendation": dossier["recommendation"],
        "entities": dossier.get("entities", {}),
        "modalities": {
            "asr": len(raw["transcript"]) > 0,
            "ocr": len(raw["ocr"]) > 0,
            "vision": len(raw["visual"]) > 0,
        },
        "discovered_at": item.discovered_at,
        "status": "pending_review",
        "analyst_comment": None,
    }


def append_to_queue(record: dict) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_forever():
    logger.info("Collector started. Polling %d connectors every %ds.", len(CONNECTORS), POLL_INTERVAL_SECONDS)
    while True:
        for connector in CONNECTORS:
            try:
                items = connector.poll()
            except Exception as e:  # noqa: BLE001
                logger.exception("connector %s failed this cycle: %s", connector.name, e)
                continue
            for item in items:
                logger.info("new item from %s: %s", connector.name, item.item_id)
                record = process_item(item)
                append_to_queue(record)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()
