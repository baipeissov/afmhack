"""Простое персистентное хранилище уже обработанных id (дедупликация
между опросами Collector'а). JSON-файл достаточен для объёма хакатона —
не тащим Redis/Postgres ради MVP."""

import json
from pathlib import Path


class SeenStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seen: set[str] = set()
        if self.path.exists():
            self._seen = set(json.loads(self.path.read_text() or "[]"))

    def is_new(self, item_id: str) -> bool:
        return item_id not in self._seen

    def mark_seen(self, item_id: str) -> None:
        self._seen.add(item_id)
        self.path.write_text(json.dumps(sorted(self._seen)))
