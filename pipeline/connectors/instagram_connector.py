"""
Коннектор к публичным Instagram-постам через `yt-dlp`.

ВАЖНО (честно говорим это на защите, не прячем ограничение): Instagram
значительно агрессивнее TikTok блокирует анонимный доступ — хэштег-поиск
без логина у Instagram, как правило, недоступен публично уже несколько лет.
Поэтому этот коннектор реализован в режиме "по списку публичных URL"
(аналитик/жалоба гражданина даёт прямую ссылку на публичный пост/reels),
а НЕ автономного хэштег-краулинга, как у TikTok.

Это совпадает с тем, как должен работать продовый Instagram Graph API
коннектор: Graph API тоже не отдаёт произвольный хэштег-поиск без
business-аккаунта и approval — там тоже работа идёт через явно заданные
объекты (media id / business discovery), а не "слушай весь Instagram".
"""

import logging
from pathlib import Path

from .base import Connector, DiscoveredItem
from .seen_store import SeenStore

logger = logging.getLogger("collector.instagram")

INCOMING_DIR = Path(__file__).resolve().parents[2] / "data" / "incoming"
SEEN_DB = Path(__file__).resolve().parents[2] / "data" / ".instagram_seen.json"


class InstagramUrlListConnector(Connector):
    """Опрашивает заранее заданный список публичных URL (приходящих, например,
    из жалоб граждан или из ручного watchlist-файла data/instagram_watchlist.txt)
    и скачивает те, что ещё не видели."""

    name = "instagram_public_url"

    def __init__(self, watchlist_file: Path | None = None, incoming_dir: Path = INCOMING_DIR):
        self.watchlist_file = Path(
            watchlist_file or Path(__file__).resolve().parents[2] / "data" / "instagram_watchlist.txt"
        )
        self.incoming_dir = Path(incoming_dir)
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.seen = SeenStore(SEEN_DB)

    def _read_urls(self) -> list[str]:
        if not self.watchlist_file.exists():
            return []
        lines = self.watchlist_file.read_text(encoding="utf-8").splitlines()
        return [u.strip() for u in lines if u.strip() and not u.startswith("#")]

    def poll(self) -> list[DiscoveredItem]:
        import yt_dlp

        discovered = []
        for url in self._read_urls():
            if not self.seen.is_new(url):
                continue

            out_template = str(self.incoming_dir / "instagram_%(id)s.%(ext)s")
            opts = {
                "quiet": True,
                "no_warnings": True,
                "format": "mp4/best",
                "outtmpl": out_template,
            }
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    local_path = ydl.prepare_filename(info)
            except Exception as e:  # noqa: BLE001
                logger.warning("instagram download failed for %s: %s", url, e)
                continue

            self.seen.mark_seen(url)
            discovered.append(
                DiscoveredItem(
                    item_id=f"instagram_{info.get('id', url)}",
                    source=self.name,
                    url=url,
                    local_path=local_path,
                    caption=info.get("description", ""),
                    account_handle=info.get("uploader"),
                )
            )
        return discovered
