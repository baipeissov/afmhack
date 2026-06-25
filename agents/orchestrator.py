"""
SunkarOrchestrator v2 — координатор реального агентного слоя.

В отличие от прежней версии в backend/orchestrator.py (заглушки Collector/
Analyzer + своя очередь), эта версия работает с НАСТОЯЩИМ пайплайном
(api/dossier.build_dossier через AnalysisAgent) и ОБЩЕЙ очередью
data/risk_queue.jsonl, а также держит накапливаемый граф связей.

Тяжёлые импорты (build_dossier) — ленивые, поэтому оркестратор и его лёгкие
эндпоинты грузятся и без полного ML-стека. Фоновые циклы запускаются опционально
(api/main.py стартует их только при SUNKAR_ORCHESTRATOR=true).
"""

from __future__ import annotations

import asyncio
import logging

from .base import Agent, read_queue
from .dataset.curator import DatasetCuratorAgent
from .dataset.retrainer import RetrainerAgent
from .discovery.discovery_agent import DiscoveryAgent
from .engagement.engagement_agent import EngagementAgent
from .liaison.liaison_agent import LiaisonAgent
from .network import NetworkMapper, PredictiveScorer
from .specialists.router import SpecialistRouter

log = logging.getLogger("sunkar.orchestrator")

COLLECTION_INTERVAL = 60   # сек между циклами обнаружения
NETWORK_INTERVAL = 1800    # пересчёт центральности


def _account_from_record(rec: dict) -> dict:
    return {
        "handle": rec.get("account_handle"),
        "platform": rec.get("platform", "tiktok"),
        "risk_score": rec.get("risk_score", 0.0),
        "violation_class": rec.get("top_class", "clean"),
        "followers": rec.get("followers", 0),
        "created_at": rec.get("discovered_at", ""),
        "caption": rec.get("caption", ""),
        "bio": rec.get("caption", ""),
    }


class SunkarOrchestrator(Agent):
    name = "orchestrator"

    def __init__(self) -> None:
        self.discovery = DiscoveryAgent()
        self.specialists = SpecialistRouter()
        self.network = NetworkMapper()
        self.predictor = PredictiveScorer()
        self.curator = DatasetCuratorAgent()
        self.retrainer = RetrainerAgent()
        self.engagement = EngagementAgent()
        self.liaison = LiaisonAgent()
        self._seed_network_from_queue()

    # ── общий граф ──
    def _seed_network_from_queue(self) -> None:
        for rec in read_queue():
            if rec.get("account_handle") and rec["account_handle"] != "unknown":
                self.network.add_account(_account_from_record(rec))

    def ingest_record(self, rec: dict) -> None:
        if rec.get("account_handle") and rec["account_handle"] != "unknown":
            acc = _account_from_record(rec)
            self.network.add_account(acc)
            rec.setdefault("network_connections", self.network.find_connections(acc))

    # ── один цикл (для эндпоинта /discovery/run и демо) ──
    def cycle_once(self, run_specialists: bool = True) -> dict:
        records = self.discovery.discover_and_analyze()
        enriched = 0
        for rec in records:
            self.ingest_record(rec)
            if run_specialists and rec.get("risk_score", 0) >= 0.5:
                self.specialists.run(rec["item_id"])
                enriched += 1
        self.log_action("cycle", discovered=len(records), enriched=enriched)
        return {"discovered": len(records), "enriched": enriched,
                "items": [r["item_id"] for r in records]}

    # ── фоновые циклы ──
    async def collection_loop(self) -> None:
        while True:
            try:
                await asyncio.to_thread(self.cycle_once)
            except Exception as e:  # noqa: BLE001
                log.exception("collection cycle error: %s", e)
            await asyncio.sleep(COLLECTION_INTERVAL)

    async def network_loop(self) -> None:
        while True:
            await asyncio.sleep(NETWORK_INTERVAL)
            central = self.network.get_central_accounts(3)
            log.info("Граф: %d узлов; центр: %s", len(self.network.graph),
                     ", ".join(c["handle"] for c in central) or "—")

    async def run(self) -> None:
        log.info("СУНКАР orchestrator: старт фоновых циклов")
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.collection_loop())
            tg.create_task(self.network_loop())


# Синглтон для роутера/эндпоинтов.
orchestrator = SunkarOrchestrator()
