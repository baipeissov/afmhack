"""
Browser-коннектор TikTok на Playwright.

В отличие от yt-dlp `extract_flat` (только лёгкий список по хэштегу), реальный
headless-браузер умеет ЛИСТАТЬ и ИСКАТЬ: открывает страницу хэштега или
поисковый запрос, прокручивает ленту, собирает ссылки на видео + подписи,
затем скачивает найденное через yt-dlp.

Этический периметр (как у штатных коннекторов):
  - только публичные страницы (хэштег/поиск), видимые без логина;
  - НЕ логинимся, НЕ решаем капчу автоматически, НЕ обходим антибот — если
    видим challenge/блок, логируем и пропускаем цикл;
  - rate-limit: ограниченное число видео за опрос, паузы между прокрутками;
  - сохраняем только нужное для анализа (видео + публичная подпись + @handle).
"""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path

from pipeline.connectors.base import Connector, DiscoveredItem
from pipeline.connectors.seen_store import SeenStore

from ._download import download_video

logger = logging.getLogger("sunkar.discovery.tiktok_browser")

ROOT = Path(__file__).resolve().parents[2]
INCOMING_DIR = ROOT / "data" / "incoming"
SEEN_DB = ROOT / "data" / ".tiktok_browser_seen.json"

# Расширенный watchlist под KZ/RU финмошенничество.
DEFAULT_WATCHLIST = [
    "казино", "ставки", "1xbet", "mostbet", "инвестиции", "пирамида",
    "пассивныйдоход", "лёгкиеденьги", "криптоинвест", "казахстанинвест",
    "заработоконлайн", "трейдинг",
]

VIDEO_HREF_RE = re.compile(r"https?://www\.tiktok\.com/@[\w.\-]+/video/(\d+)")

MAX_ITEMS_PER_POLL = int(os.getenv("TIKTOK_MAX_ITEMS", "5"))
SCROLLS_PER_PAGE = int(os.getenv("TIKTOK_SCROLLS", "4"))
HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() != "false"
PAGE_TIMEOUT_MS = 20000


class TikTokBrowserConnector(Connector):
    name = "tiktok_browser"

    def __init__(self, watchlist: list[str] | None = None, use_search: bool = False,
                 incoming_dir: Path = INCOMING_DIR):
        self.watchlist = watchlist or DEFAULT_WATCHLIST
        self.use_search = use_search  # True: /search/video?q=, False: /tag/
        self.incoming_dir = Path(incoming_dir)
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.seen = SeenStore(SEEN_DB)

    def _page_url(self, term: str) -> str:
        if self.use_search:
            return f"https://www.tiktok.com/search/video?q={term}"
        return f"https://www.tiktok.com/tag/{term}"

    def _discover_urls(self, term: str) -> list[tuple[str, str]]:
        """Возвращает [(video_url, caption_hint)] с публичной страницы.
        Playwright импортируется лениво, чтобы пакет грузился без браузера."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("playwright не установлен — браузерный коннектор пропущен")
            return []

        found: dict[str, str] = {}
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=HEADLESS)
                ctx = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                    locale="ru-RU",
                )
                page = ctx.new_page()
                try:
                    page.goto(self._page_url(term), timeout=PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
                except Exception as e:  # noqa: BLE001
                    logger.warning("tiktok '%s' недоступен (блок/таймаут): %s", term, e)
                    browser.close()
                    return []

                # challenge/captcha detection — не пытаемся обойти
                if "captcha" in page.url.lower() or page.locator("text=verify").count() > 0:
                    logger.warning("tiktok '%s': обнаружен challenge — пропускаем", term)
                    browser.close()
                    return []

                for _ in range(SCROLLS_PER_PAGE):
                    for a in page.locator("a[href*='/video/']").all():
                        href = a.get_attribute("href") or ""
                        m = VIDEO_HREF_RE.search(href)
                        if not m:
                            continue
                        cap = (a.get_attribute("aria-label") or a.inner_text() or "")[:300]
                        found.setdefault(href.split("?")[0], cap.strip())
                    page.mouse.wheel(0, 4000)
                    time.sleep(1.2)
                    if len(found) >= MAX_ITEMS_PER_POLL * 3:
                        break
                browser.close()
        except Exception as e:  # noqa: BLE001
            logger.warning("tiktok browser error for '%s': %s", term, e)
            return []
        return list(found.items())

    def poll(self) -> list[DiscoveredItem]:
        discovered: list[DiscoveredItem] = []
        for term in self.watchlist:
            if len(discovered) >= MAX_ITEMS_PER_POLL:
                break
            for url, caption_hint in self._discover_urls(term):
                m = VIDEO_HREF_RE.search(url)
                if not m:
                    continue
                item_id = f"tiktok_{m.group(1)}"
                if not self.seen.is_new(item_id):
                    continue
                dl = download_video(url, item_id, self.incoming_dir)
                self.seen.mark_seen(item_id)  # помечаем даже при неудаче, чтобы не зацикливаться
                if dl is None:
                    continue
                discovered.append(DiscoveredItem(
                    item_id=item_id,
                    source=self.name,
                    url=url,
                    local_path=dl["local_path"],
                    caption=dl["caption"] or caption_hint,
                    account_handle=dl["account_handle"],
                    metadata={"discovery": "browser", "term": term},
                ))
                if len(discovered) >= MAX_ITEMS_PER_POLL:
                    break
        return discovered


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    found = TikTokBrowserConnector().poll()
    print(f"discovered {len(found)} items")
    for it in found:
        print(" -", it.item_id, it.local_path, (it.caption or "")[:80])
