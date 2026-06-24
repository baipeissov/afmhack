"""
Коннектор очереди жалоб граждан. `POST /report` в api/main.py дописывает
строку в data/citizen_reports.jsonl; этот коннектор читает новые строки
и удаляет их из очереди (consume-once), отдавая Collector'у на обработку.

Это легитимный, не-скрейпинговый канал постоянного притока контента —
именно так АФМ получает сигналы сегодня (жалобы), просто оцифрованно.
"""

import json
from pathlib import Path

from .base import Connector, DiscoveredItem

QUEUE_PATH = Path(__file__).resolve().parents[2] / "data" / "citizen_reports.jsonl"


class CitizenReportsConnector(Connector):
    name = "citizen_report"

    def __init__(self, queue_path: Path = QUEUE_PATH):
        self.queue_path = Path(queue_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.queue_path.touch(exist_ok=True)

    def poll(self) -> list[DiscoveredItem]:
        lines = self.queue_path.read_text(encoding="utf-8").splitlines()
        if not lines:
            return []

        # consume-once: очищаем файл сразу после чтения
        self.queue_path.write_text("", encoding="utf-8")

        items = []
        for line in lines:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            items.append(
                DiscoveredItem(
                    item_id=f"report_{row['report_id']}",
                    source=self.name,
                    url=row.get("url"),
                    local_path=row.get("local_path"),
                    caption=row.get("note", ""),
                    metadata={"reporter_contact": row.get("reporter_contact")},
                )
            )
        return items
