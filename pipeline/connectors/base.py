"""
Общий интерфейс источника данных для Collector-сервиса.

Любой источник (TikTok, Instagram, жалобы граждан, в будущем — официальный
TikTok Research API / Instagram Graph API) реализует один и тот же контракт.
Collector (scripts/run_collector.py) не знает, откуда именно пришло видео —
он просто опрашивает все зарегистрированные коннекторы по таймеру.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class DiscoveredItem:
    item_id: str
    source: str
    url: Optional[str]
    local_path: Optional[str]
    caption: str = ""
    account_handle: Optional[str] = None
    discovered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict = field(default_factory=dict)


class Connector(ABC):
    name: str = "base"

    @abstractmethod
    def poll(self) -> list[DiscoveredItem]:
        """Вернуть список НОВЫХ айтемов, обнаруженных с прошлого опроса.
        Дедупликация (чтобы не возвращать одно и то же видео повторно)
        — ответственность конкретного коннектора."""
        raise NotImplementedError
