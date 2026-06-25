"""
DiscoveryAgent — гибридный скрейпинг с фоллбэком.

Стратегия (как в плане):
  1. Browser-коннекторы (Playwright) — основной канал поиска/листания.
  2. API-фоллбэк — если браузер поймал блок/0 и задан SCRAPER_API_KEY.
  3. yt-dlp хэштег/URL коннекторы — дешёвый базовый канал.
  4. Жалобы граждан (citizen_reports).
  5. Network-expansion — от подтверждённых мошеннических аккаунтов добавляем
     хэштеги/термины в watchlist браузерных коннекторов.

Каждый коннектор уже сам дедуплицирует (SeenStore). Найденное сразу гоняется
через AnalysisAgent и попадает в общий risk_queue.jsonl.
"""

from __future__ import annotations

import logging

from pipeline.connectors.base import DiscoveredItem
from pipeline.connectors.citizen_reports import CitizenReportsConnector
from pipeline.connectors.instagram_connector import InstagramUrlListConnector
from pipeline.connectors.tiktok_connector import TikTokHashtagConnector

from ..analysis import AnalysisAgent
from ..base import Agent
from .api_fallback import ApiFallbackConnector
from .browser_instagram import InstagramBrowserConnector
from .browser_tiktok import TikTokBrowserConnector

log = logging.getLogger("sunkar.discovery.agent")


class DiscoveryAgent(Agent):
    name = "discovery"

    def __init__(self) -> None:
        self.tiktok_browser = TikTokBrowserConnector()
        self.instagram_browser = InstagramBrowserConnector()
        self.tiktok_api = ApiFallbackConnector(platform="tiktok")
        self.tiktok_ytdlp = TikTokHashtagConnector()
        self.instagram_ytdlp = InstagramUrlListConnector()
        self.citizen = CitizenReportsConnector()
        self.analysis = AnalysisAgent()

    def _poll_safe(self, connector) -> list[DiscoveredItem]:
        try:
            return connector.poll()
        except Exception as e:  # noqa: BLE001
            log.warning("connector %s упал: %s", getattr(connector, "name", "?"), e)
            return []

    def expand_watchlist(self, terms: list[str]) -> None:
        """Network-expansion: добавить термины (хэштеги/ключи), найденные у
        подтверждённых мошеннических аккаунтов, к браузерным коннекторам."""
        for c in (self.tiktok_browser, self.instagram_browser):
            for t in terms:
                t = t.lstrip("#").strip().lower()
                if t and t not in c.watchlist:
                    c.watchlist.append(t)
        if terms:
            self.log_action("watchlist_expanded", added=terms)

    def discover(self) -> list[DiscoveredItem]:
        """Опрашивает все каналы с фоллбэком. Возвращает новые айтемы."""
        items: list[DiscoveredItem] = []

        # TikTok: браузер → (если пусто) API-фоллбэк → yt-dlp как базовый
        tk = self._poll_safe(self.tiktok_browser)
        if not tk and self.tiktok_api.enabled:
            log.info("TikTok browser пусто/блок — пробуем API-фоллбэк")
            tk = self._poll_safe(self.tiktok_api)
        items += tk
        items += self._poll_safe(self.tiktok_ytdlp)

        # Instagram: браузер → yt-dlp watchlist
        items += self._poll_safe(self.instagram_browser)
        items += self._poll_safe(self.instagram_ytdlp)

        # Жалобы граждан
        items += self._poll_safe(self.citizen)

        self.log_action("discovered", count=len(items),
                        sources=sorted({i.source for i in items}))
        return items

    def discover_and_analyze(self) -> list[dict]:
        """Полный цикл: обнаружить → проанализировать → записать в risk_queue."""
        records = []
        for item in self.discover():
            rec = self.analysis.analyze_item(item)
            if rec:
                records.append(rec)
        return records
