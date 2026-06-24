"""
Реальный коннектор к публичным TikTok-страницам по хэштегам/ключевым словам,
через `yt-dlp` (без логина, без обхода капч/антибота — если yt-dlp получает
captcha/блок, мы просто логируем и пропускаем цикл, НЕ пытаемся обойти
защиту платформы).

Этический периметр (важно для критерия #3 на защите):
  - читаем ТОЛЬКО публичные хэштег-страницы (то, что видно без аккаунта);
  - никакого логина, никакой имитации человека, никакого обхода rate-limit;
  - сохраняем только то, что нужно для анализа контента (видео + публичный
    caption + публичный @handle) — НЕ собираем подписчиков, личные данные,
    геолокацию и т.п.;
  - частота опроса и число видео за цикл намеренно ограничены
    (POLL_INTERVAL_SECONDS, MAX_ITEMS_PER_POLL) — это мониторинг, не массовый
    краулинг.

Watchlist хэштегов/ключевых слов — это и есть наш "запрос" к публичному
контенту, аналог того, что вручную делает аналитик АФМ сегодня, только
автоматически и непрерывно.
"""

import logging
import time
from pathlib import Path

from .base import Connector, DiscoveredItem
from .seen_store import SeenStore

logger = logging.getLogger("collector.tiktok")

DEFAULT_WATCHLIST = [
    "казино",
    "ставки",
    "инвестиции",
    "пирамида",
    "гарантированныйдоход",
    "казахстанинвест",
]

INCOMING_DIR = Path(__file__).resolve().parents[2] / "data" / "incoming"
SEEN_DB = Path(__file__).resolve().parents[2] / "data" / ".tiktok_seen.json"

MAX_ITEMS_PER_POLL = 5          # не более N новых видео за один цикл опроса
REQUEST_SLEEP_SECONDS = 2.0      # пауза между запросами к разным хэштегам
MAX_VIDEO_DURATION_SECONDS = 600  # не скачиваем нетипично длинные видео


class TikTokHashtagConnector(Connector):
    name = "tiktok_public_hashtag"

    def __init__(self, watchlist=None, incoming_dir: Path = INCOMING_DIR):
        self.watchlist = watchlist or DEFAULT_WATCHLIST
        self.incoming_dir = Path(incoming_dir)
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.seen = SeenStore(SEEN_DB)

    def _list_hashtag_videos(self, tag: str) -> list[dict]:
        """Список видео с публичной хэштег-страницы без скачивания
        (extract_flat) — лёгкий запрос для обнаружения новых id."""
        import yt_dlp

        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
            "playlistend": MAX_ITEMS_PER_POLL,
        }
        url = f"https://www.tiktok.com/tag/{tag}"
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            return info.get("entries") or []
        except Exception as e:  # noqa: BLE001
            # Платформа может отдать captcha/блок/изменить разметку страницы —
            # это ожидаемо для публичного скрейпинга. Не ретраим агрессивно,
            # не пытаемся обойти защиту, просто логируем и идём дальше.
            logger.warning("tiktok hashtag '%s' unavailable this cycle: %s", tag, e)
            return []

    def _download(self, entry: dict) -> DiscoveredItem | None:
        import yt_dlp

        video_id = str(entry.get("id"))
        video_url = entry.get("url") or entry.get("webpage_url")
        if not video_id or not video_url:
            return None

        out_template = str(self.incoming_dir / f"tiktok_{video_id}.%(ext)s")
        opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "mp4/best",
            "outtmpl": out_template,
            "match_filter": yt_dlp.utils.match_filter_func(
                f"duration < {MAX_VIDEO_DURATION_SECONDS}"
            ),
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                local_path = ydl.prepare_filename(info)
        except Exception as e:  # noqa: BLE001
            logger.warning("tiktok download failed for %s: %s", video_id, e)
            return None

        return DiscoveredItem(
            item_id=f"tiktok_{video_id}",
            source=self.name,
            url=video_url,
            local_path=local_path,
            caption=info.get("description", "") if isinstance(info, dict) else "",
            account_handle=info.get("uploader") if isinstance(info, dict) else None,
            metadata={"hashtag_watchlist_hit": True},
        )

    def poll(self) -> list[DiscoveredItem]:
        discovered: list[DiscoveredItem] = []
        for tag in self.watchlist:
            if len(discovered) >= MAX_ITEMS_PER_POLL:
                break
            for entry in self._list_hashtag_videos(tag):
                video_id = f"tiktok_{entry.get('id')}"
                if not self.seen.is_new(video_id):
                    continue
                item = self._download(entry)
                if item is None:
                    continue
                self.seen.mark_seen(video_id)
                discovered.append(item)
                if len(discovered) >= MAX_ITEMS_PER_POLL:
                    break
            time.sleep(REQUEST_SLEEP_SECONDS)
        return discovered


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    connector = TikTokHashtagConnector()
    found = connector.poll()
    print(f"discovered {len(found)} new items")
    for it in found:
        print(" -", it.item_id, it.local_path, it.caption[:80])
