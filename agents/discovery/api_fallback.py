"""
Фоллбэк-коннектор через стороннее scraping-API (Apify / RapidAPI / Bright Data).

Включается, ТОЛЬКО если заданы SCRAPER_API_PROVIDER и SCRAPER_API_KEY в .env.
По умолчанию выключен (возвращает []), чтобы система работала и без платного
ключа. Это «страховка», когда браузерный коннектор поймал блок.

Провайдер-специфичные детали вынесены в _fetch_*; добавить нового провайдера =
реализовать ещё один _fetch_<provider>, возвращающий список
{video_url, caption, handle}.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

from pipeline.connectors.base import Connector, DiscoveredItem
from pipeline.connectors.seen_store import SeenStore

from ._download import download_video

logger = logging.getLogger("sunkar.discovery.api_fallback")

ROOT = Path(__file__).resolve().parents[2]
INCOMING_DIR = ROOT / "data" / "incoming"
SEEN_DB = ROOT / "data" / ".api_fallback_seen.json"
MAX_ITEMS_PER_POLL = int(os.getenv("APIFALLBACK_MAX_ITEMS", "5"))


class ApiFallbackConnector(Connector):
    name = "api_fallback"

    def __init__(self, platform: str = "tiktok", terms: list[str] | None = None,
                 incoming_dir: Path = INCOMING_DIR):
        self.platform = platform
        self.terms = terms or ["казино", "инвестиции", "пирамида"]
        self.incoming_dir = Path(incoming_dir)
        self.seen = SeenStore(SEEN_DB)
        self.provider = (os.getenv("SCRAPER_API_PROVIDER") or "").lower()
        self.api_key = os.getenv("SCRAPER_API_KEY") or ""

    @property
    def enabled(self) -> bool:
        return bool(self.provider and self.api_key)

    def _fetch_rapidapi(self, term: str) -> list[dict]:
        """Пример для RapidAPI-эндпоинта поиска TikTok. Хост/путь зависят от
        конкретной подписки — настраивается через SCRAPER_API_HOST."""
        host = os.getenv("SCRAPER_API_HOST", "tiktok-scraper7.p.rapidapi.com")
        url = f"https://{host}/feed/search"
        headers = {"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": host}
        try:
            with httpx.Client(timeout=30) as c:
                r = c.get(url, headers=headers, params={"keywords": term, "count": MAX_ITEMS_PER_POLL})
            r.raise_for_status()
            data = r.json()
        except Exception as e:  # noqa: BLE001
            logger.warning("rapidapi fetch failed for '%s': %s", term, e)
            return []
        items = []
        for v in (data.get("data", {}).get("videos") or data.get("videos") or [])[:MAX_ITEMS_PER_POLL]:
            url = v.get("play") or v.get("video_url") or v.get("url")
            if url:
                items.append({
                    "video_url": url,
                    "caption": v.get("title") or v.get("desc") or "",
                    "handle": (v.get("author") or {}).get("unique_id") if isinstance(v.get("author"), dict) else None,
                    "id": str(v.get("video_id") or v.get("aweme_id") or v.get("id") or ""),
                })
        return items

    def _fetch(self, term: str) -> list[dict]:
        if self.provider == "rapidapi":
            return self._fetch_rapidapi(term)
        logger.warning("Неизвестный SCRAPER_API_PROVIDER=%r — фоллбэк выключен", self.provider)
        return []

    def poll(self) -> list[DiscoveredItem]:
        if not self.enabled:
            return []
        discovered: list[DiscoveredItem] = []
        for term in self.terms:
            if len(discovered) >= MAX_ITEMS_PER_POLL:
                break
            for v in self._fetch(term):
                vid = v.get("id") or v["video_url"].rsplit("/", 1)[-1]
                item_id = f"{self.platform}_api_{vid}"
                if not self.seen.is_new(item_id):
                    continue
                dl = download_video(v["video_url"], item_id, self.incoming_dir)
                self.seen.mark_seen(item_id)
                if dl is None:
                    # некоторые API отдают прямой mp4-URL — тогда местного скачивания нет,
                    # но build_dossier нужен файл, поэтому без файла пропускаем.
                    continue
                discovered.append(DiscoveredItem(
                    item_id=item_id,
                    source=self.name,
                    url=v["video_url"],
                    local_path=dl["local_path"],
                    caption=dl["caption"] or v.get("caption", ""),
                    account_handle=dl["account_handle"] or v.get("handle"),
                    metadata={"discovery": "api_fallback", "provider": self.provider, "term": term},
                ))
        return discovered
