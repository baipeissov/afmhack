"""
Browser-коннектор Instagram на Playwright.

Открывает публичную страницу хэштега (instagram.com/explore/tags/{tag}/),
прокручивает, собирает ссылки на посты/reels, затем скачивает медиа + подпись
через yt-dlp.

Важно: Instagram особенно агрессивно требует логин и отдаёт challenge
анонимным клиентам. Мы НЕ логинимся и НЕ обходим это — если видим login-wall
или challenge, честно пропускаем (фоллбэк на API-коннектор/жалобы граждан).
Этический периметр тот же, что у TikTok-коннектора.
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

logger = logging.getLogger("sunkar.discovery.instagram_browser")

ROOT = Path(__file__).resolve().parents[2]
INCOMING_DIR = ROOT / "data" / "incoming"
SEEN_DB = ROOT / "data" / ".instagram_browser_seen.json"

DEFAULT_WATCHLIST = [
    "казино", "ставки", "инвестиции", "пирамида", "пассивныйдоход",
    "инвестициикз", "заработок", "криптокз",
]

POST_HREF_RE = re.compile(r"/(p|reel)/([A-Za-z0-9_\-]+)/")

MAX_ITEMS_PER_POLL = int(os.getenv("INSTAGRAM_MAX_ITEMS", "5"))
SCROLLS_PER_PAGE = int(os.getenv("INSTAGRAM_SCROLLS", "4"))
HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() != "false"
PAGE_TIMEOUT_MS = 20000


class InstagramBrowserConnector(Connector):
    name = "instagram_browser"

    def __init__(self, watchlist: list[str] | None = None, incoming_dir: Path = INCOMING_DIR):
        self.watchlist = watchlist or DEFAULT_WATCHLIST
        self.incoming_dir = Path(incoming_dir)
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.seen = SeenStore(SEEN_DB)

    def _discover_urls(self, tag: str) -> list[str]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("playwright не установлен — IG браузерный коннектор пропущен")
            return []

        urls: set[str] = set()
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=HEADLESS)
                ctx = browser.new_context(locale="ru-RU")
                page = ctx.new_page()
                try:
                    page.goto(f"https://www.instagram.com/explore/tags/{tag}/",
                              timeout=PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
                except Exception as e:  # noqa: BLE001
                    logger.warning("instagram '%s' недоступен: %s", tag, e)
                    browser.close()
                    return []

                if "/accounts/login" in page.url or page.locator("text=Log in").count() > 3:
                    logger.warning("instagram '%s': login-wall — пропускаем (фоллбэк)", tag)
                    browser.close()
                    return []

                for _ in range(SCROLLS_PER_PAGE):
                    for a in page.locator("a[href*='/p/'], a[href*='/reel/']").all():
                        href = a.get_attribute("href") or ""
                        m = POST_HREF_RE.search(href)
                        if m:
                            urls.add(f"https://www.instagram.com/{m.group(1)}/{m.group(2)}/")
                    page.mouse.wheel(0, 4000)
                    time.sleep(1.2)
                    if len(urls) >= MAX_ITEMS_PER_POLL * 3:
                        break
                browser.close()
        except Exception as e:  # noqa: BLE001
            logger.warning("instagram browser error for '%s': %s", tag, e)
            return []
        return list(urls)

    def poll(self) -> list[DiscoveredItem]:
        discovered: list[DiscoveredItem] = []
        for tag in self.watchlist:
            if len(discovered) >= MAX_ITEMS_PER_POLL:
                break
            for url in self._discover_urls(tag):
                m = POST_HREF_RE.search(url)
                if not m:
                    continue
                item_id = f"instagram_{m.group(2)}"
                if not self.seen.is_new(item_id):
                    continue
                dl = download_video(url, item_id, self.incoming_dir)
                self.seen.mark_seen(item_id)
                if dl is None:
                    continue
                discovered.append(DiscoveredItem(
                    item_id=item_id,
                    source=self.name,
                    url=url,
                    local_path=dl["local_path"],
                    caption=dl["caption"],
                    account_handle=dl["account_handle"],
                    metadata={"discovery": "browser", "tag": tag},
                ))
                if len(discovered) >= MAX_ITEMS_PER_POLL:
                    break
        return discovered
