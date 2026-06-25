"""
Базовые примитивы агентного слоя: общий путь к данным, append-only аудит,
результат работы агента.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Единый источник истины — те же файлы, что использует api/main.py.
RISK_QUEUE = DATA_DIR / "risk_queue.jsonl"
AUDIT_LOG = DATA_DIR / "audit_log.jsonl"

log = logging.getLogger("sunkar.agents")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def audit(event: str, **fields: Any) -> None:
    """Неизменяемая дозапись в общий журнал аудита (JSON Lines)."""
    rec = {"ts": now_iso(), "event": event, **fields}
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def write_jsonl(path: Path, items: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, item: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def read_queue() -> list[dict]:
    return read_jsonl(RISK_QUEUE)


def get_case(item_id: str) -> dict | None:
    for it in read_queue():
        if it.get("item_id") == item_id:
            return it
    return None


def update_case(item_id: str, patch: dict) -> dict | None:
    items = read_queue()
    updated = None
    for it in items:
        if it.get("item_id") == item_id:
            it.update(patch)
            updated = it
    if updated is not None:
        write_jsonl(RISK_QUEUE, items)
    return updated


@dataclass
class AgentResult:
    agent: str
    ok: bool
    summary: str
    data: dict = field(default_factory=dict)
    ts: str = field(default_factory=now_iso)

    def to_dict(self) -> dict:
        return asdict(self)


class Agent:
    """База агента: имя + аудит + единый доступ к очереди кейсов."""

    name: str = "agent"

    def log_action(self, event: str, **fields: Any) -> None:
        audit(f"{self.name}.{event}", agent=self.name, **fields)
