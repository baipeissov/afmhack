"""
orchestrator.py — центральный координатор мультиагентной системы СУНКАР.

SunkarOrchestrator на asyncio параллельно ведёт несколько агентов:
  • Агент 0 — PredictiveScorer  : упреждающая оценка молодых аккаунтов
  • Агент 1 — Collector         : сбор новых видео/аккаунтов (существует)
  • Агент 2 — VideoAnalyzer     : анализ контента, risk_score (существует)
  • Агент 3 — ProbeAgent        : сбор доказательств после одобрения аналитика
  • Агент 4 — NetworkMapper     : граф связей мошеннической сети
  • Агент 5 — AFMReportGenerator: официальный рапорт АФМ (DOCX)

Запуск:
    uvicorn backend.orchestrator:app --reload --port 8080
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("sunkar")

# ── существующие агенты (probe / report) ──
try:  # пакетный импорт (uvicorn backend.orchestrator:app)
    from .probe_agent import ProbeAgent
    from .report_generator import AFMReportGenerator
except ImportError:  # запуск как скрипт из каталога backend/
    from probe_agent import ProbeAgent  # type: ignore
    from report_generator import AFMReportGenerator  # type: ignore


# ───────────────────────── паттерны для связей ─────────────────────────

TELEGRAM_RE = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me)/[A-Za-z0-9_+/]+", re.I)
HASHTAG_RE = re.compile(r"#([A-Za-z0-9_а-яёА-ЯЁ]+)")
MENTION_RE = re.compile(r"@([A-Za-z0-9_.]+)")
URL_RE = re.compile(r"https?://[^\s)]+", re.I)


def _norm_tg(link: str) -> str:
    link = link.lower()
    return link.split("t.me/")[-1].split("telegram.me/")[-1].strip("/")


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


# ════════════════════════ Агент 4 — NetworkMapper ════════════════════════

class NetworkMapper:
    """Строит и анализирует граф связей мошеннической сети."""

    def __init__(self) -> None:
        self.graph: dict[str, dict] = {}  # handle -> {connections: [], metadata: {}}

    def add_account(self, account: dict) -> None:
        handle = account.get("handle", "").lstrip("@")
        if not handle:
            return
        self.graph[handle] = self.graph.get(handle, {"connections": [], "metadata": {}})
        self.graph[handle]["metadata"] = account

    # ── извлечение сигналов из текста аккаунта ──
    @staticmethod
    def _signals(account: dict) -> dict[str, set[str]]:
        text = " ".join(
            str(account.get(k, "") or "")
            for k in ("bio", "bio_text", "caption", "url", "bio_url")
        )
        telegram = {_norm_tg(m.group(0)) for m in TELEGRAM_RE.finditer(text)}
        if account.get("telegram"):
            telegram.add(_norm_tg(str(account["telegram"])))
        referrals = {u for u in URL_RE.findall(text) if "ref" in u.lower()}
        if account.get("referral"):
            referrals.add(str(account["referral"]))
        hashtags = {h.lower() for h in HASHTAG_RE.findall(text)} | {
            str(h).lstrip("#").lower() for h in (account.get("hashtags") or [])
        }
        mentions = {m.lower() for m in MENTION_RE.findall(text)} | {
            str(m).lstrip("@").lower() for m in (account.get("mentions") or [])
        }
        # не считаем сам аккаунт упоминанием себя
        mentions.discard(account.get("handle", "").lstrip("@").lower())
        return {"telegram": telegram, "referral": referrals, "hashtags": hashtags, "mentions": mentions}

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def find_connections(self, account: dict) -> list[dict]:
        """Ищет связи аккаунта со всеми остальными в графе."""
        handle = account.get("handle", "").lstrip("@")
        sa = self._signals(account)
        out: list[dict] = []
        for other, data in self.graph.items():
            if other == handle:
                continue
            sb = self._signals(data["metadata"])

            shared_tg = sa["telegram"] & sb["telegram"]
            if shared_tg:
                out.append({"handle": other, "link_type": "shared_telegram",
                            "strength": 0.9, "shared": sorted(shared_tg)})

            shared_ref = sa["referral"] & sb["referral"]
            if shared_ref:
                out.append({"handle": other, "link_type": "shared_referral_link",
                            "strength": 0.8, "shared": sorted(shared_ref)})

            jac = self._jaccard(sa["hashtags"], sb["hashtags"])
            if jac > 0.5:
                out.append({"handle": other, "link_type": "shared_hashtag",
                            "strength": round(jac, 2), "shared": sorted(sa["hashtags"] & sb["hashtags"])})

            shared_men = sa["mentions"] & sb["mentions"]
            if shared_men:
                strength = min(0.7, 0.3 + 0.1 * len(shared_men))
                out.append({"handle": other, "link_type": "shared_mention",
                            "strength": round(strength, 2), "shared": sorted(shared_men)})
        # сохраняем в графе
        if handle in self.graph:
            self.graph[handle]["connections"] = out
        return out

    # ── граф для React Force Graph ──
    def _all_links(self) -> list[dict]:
        seen: set[tuple] = set()
        links: list[dict] = []
        for handle, data in self.graph.items():
            for c in self.find_connections(data["metadata"]):
                a, b = sorted((handle, c["handle"]))
                key = (a, b, c["link_type"])
                if key in seen:
                    continue
                seen.add(key)
                links.append({"source": a, "target": b,
                              "link_type": c["link_type"], "strength": c["strength"]})
        return links

    def to_graph_json(self) -> dict:
        """{nodes: [], links: []} в формате фронтенда NetworkGraph."""
        nodes = []
        for handle, data in self.graph.items():
            m = data["metadata"]
            nodes.append({
                "id": handle,
                "platform": m.get("platform", "tiktok"),
                "risk_score": float(m.get("risk_score", 0.0)),
                "violation_class": m.get("violation_class", "clean"),
                "followers": int(m.get("followers", 0)),
                "created_at": str(m.get("created_at", "")),
            })
        return {"nodes": nodes, "links": self._all_links()}

    # ── PageRank: центральные узлы ──
    def get_central_accounts(self, top_n: int = 3) -> list[dict]:
        ids = list(self.graph.keys())
        if not ids:
            return []
        links = self._all_links()
        adj: dict[str, list[tuple[str, float]]] = {i: [] for i in ids}
        for l in links:
            adj[l["source"]].append((l["target"], l["strength"]))
            adj[l["target"]].append((l["source"], l["strength"]))

        N = len(ids)
        rank = {i: 1 / N for i in ids}
        d = 0.85
        for _ in range(50):
            nxt = {i: (1 - d) / N for i in ids}
            for i in ids:
                edges = adj[i]
                total = sum(w for _, w in edges)
                if total == 0:
                    for j in ids:
                        nxt[j] += d * rank[i] / N
                else:
                    for to, w in edges:
                        nxt[to] += d * rank[i] * (w / total)
            rank = nxt

        top = sorted(rank.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
        return [{
            "handle": h,
            "centrality": round(r, 4),
            "risk_score": float(self.graph[h]["metadata"].get("risk_score", 0.0)),
            "platform": self.graph[h]["metadata"].get("platform", "tiktok"),
        } for h, r in top]


# ════════════════════════ Агент 0 — PredictiveScorer ════════════════════════

class PredictiveScorer:
    """Упреждающая оценка: предсказывает риск молодого аккаунта до явных сигналов."""

    RISK_TERMS = ["доход", "гарант", "депозит", "вывод", "реферал", "пригласи",
                  "инвест", "казино", "ставк", "бонус", "%", "t.me/", "пассивн"]

    def score(self, account: dict) -> float:
        text = " ".join(str(account.get(k, "") or "") for k in ("bio", "bio_text", "caption")).lower()
        score = 0.0
        hits = sum(1 for t in self.RISK_TERMS if t in text)
        score += min(0.6, hits * 0.12)

        # молодой аккаунт — выше подозрение
        created = _parse_dt(account.get("created_at"))
        if created:
            age_days = (datetime.now(timezone.utc) - created).days
            if age_days < 7:
                score += 0.25
            elif age_days < 30:
                score += 0.15

        # аномалия: много подписчиков у очень молодого аккаунта
        followers = int(account.get("followers", 0) or 0)
        if created and (datetime.now(timezone.utc) - created).days < 30 and followers > 30000:
            score += 0.2

        return round(min(score, 1.0), 3)


# ═══════════════ Агенты 1 и 2 — заглушки (интеграционные точки) ═══════════════
# Реальные Collector / VideoAnalyzer подключаются через backend.collector /
# backend.video_analyzer; ниже — рабочие заглушки на демо-данных.

try:
    from .collector import Collector  # type: ignore
    from .video_analyzer import VideoAnalyzer  # type: ignore
except ImportError:

    _DEMO_ACCOUNTS = [
        {"handle": "quick_profit_official", "platform": "tiktok", "followers": 210000,
         "created_at": "2024-09-12", "risk_score": 0.95, "violation_class": "pyramid_investment",
         "bio": "Удвоим депозит 💸 100% гарантия вывода. Канал t.me/quick_profit_kz #инвестиции #доход"},
        {"handle": "easy_earn_kz", "platform": "tiktok", "followers": 145000,
         "created_at": "2024-10-03", "risk_score": 0.92, "violation_class": "pyramid_investment",
         "bio": "Пассивный доход 30% в месяц. t.me/quick_profit_kz #инвестиции #доход @quick_profit_official"},
        {"handle": "casino_win_astana", "platform": "instagram", "followers": 98000,
         "created_at": "2024-08-21", "risk_score": 0.88, "violation_class": "casino_betting",
         "bio": "Бонус на первый депозит! t.me/quick_profit_kz #ставки #казино"},
        {"handle": "bet_master_kz", "platform": "tiktok", "followers": 67000,
         "created_at": "2024-11-15", "risk_score": 0.84, "violation_class": "casino_betting",
         "bio": "Лучшие ставки. Вывод за 5 минут. t.me/quick_profit_kz #ставки #казино"},
        {"handle": "referral_king_kz", "platform": "tiktok", "followers": 33000,
         "created_at": "2024-12-19", "risk_score": 0.72, "violation_class": "referral_network",
         "bio": "Пригласи друга — получи бонус. https://ref.example/r/king #доход @easy_earn_kz"},
        {"handle": "food_blogger_kz", "platform": "tiktok", "followers": 120000,
         "created_at": "2022-11-28", "risk_score": 0.08, "violation_class": "clean",
         "bio": "Рецепты и обзоры кафе Алматы 🍜 #еда #алматы"},
    ]

    class Collector:  # noqa: D401 — заглушка Агента 1
        """Заглушка коллектора: выдаёт демо-видео и недавние аккаунты."""

        def __init__(self) -> None:
            self._idx = 0

        async def fetch_new_videos(self) -> list[dict]:
            await asyncio.sleep(0)  # имитация I/O
            if self._idx >= len(_DEMO_ACCOUNTS):
                return []
            acc = _DEMO_ACCOUNTS[self._idx]
            self._idx += 1
            return [{"video_id": f"v_{acc['handle']}", "account": acc, "caption": acc["bio"]}]

        async def recent_accounts(self, max_age_days: int = 30) -> list[dict]:
            await asyncio.sleep(0)
            now = datetime.now(timezone.utc)
            res = []
            for acc in _DEMO_ACCOUNTS:
                created = _parse_dt(acc.get("created_at"))
                if created and (now - created).days <= max_age_days:
                    res.append(acc)
            return res

    @dataclass
    class AnalysisResult:
        account: dict
        risk_score: float
        violation_class: str
        evidence: list[dict] = field(default_factory=list)

    class VideoAnalyzer:  # noqa: D401 — заглушка Агента 2
        """Заглушка анализатора видео: эвристика по тексту."""

        async def analyze(self, video: dict) -> "AnalysisResult":
            await asyncio.sleep(0)
            acc = video.get("account", {})
            return AnalysisResult(
                account=acc,
                risk_score=float(acc.get("risk_score", 0.0)),
                violation_class=acc.get("violation_class", "clean"),
                evidence=[{
                    "timestamp": "00:00:10",
                    "type": "ocr",
                    "description": f"Маркеры манипуляции в описании @{acc.get('handle')}",
                    "confidence": 0.85,
                    "screenshot_path": None,
                }],
            )


# ════════════════════════ Координатор ════════════════════════

class SunkarOrchestrator:
    def __init__(self) -> None:
        self.collector = Collector()              # Агент 1
        self.analyzer = VideoAnalyzer()           # Агент 2
        self.probe_agent = ProbeAgent()           # Агент 3
        self.network_mapper = NetworkMapper()     # Агент 4
        self.report_gen = AFMReportGenerator()    # Агент 5
        self.predictor = PredictiveScorer()       # Агент 0

        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.cases: dict[str, dict] = {}          # case_id -> case
        self.flagged: dict[str, dict] = {}        # ожидают решения аналитика
        self._case_seq = 2040

    # ── основной бесконечный цикл ──
    async def run_pipeline(self) -> None:
        log.info("СУНКАР: запуск пайплайна (4 параллельных контура)")
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._guard(self.collection_loop, "collection"))
            tg.create_task(self._guard(self.analysis_loop, "analysis"))
            tg.create_task(self._guard(self.prediction_loop, "prediction"))
            tg.create_task(self._guard(self.network_update_loop, "network"))

    async def _guard(self, loop_fn, name: str) -> None:
        """Не даём одному контуру уронить всю TaskGroup из-за разовой ошибки."""
        while True:
            try:
                await loop_fn()
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.exception("Контур %s упал: %s — перезапуск через 5с", name, exc)
                await asyncio.sleep(5)

    # ── контуры ──
    async def collection_loop(self) -> None:
        while True:
            videos = await self.collector.fetch_new_videos()
            for v in videos:
                await self.analysis_queue.put(v)
                acc = v.get("account")
                if acc:
                    self.network_mapper.add_account(acc)  # пополняем граф
            if videos:
                log.info("Коллектор: +%d видео в очередь анализа", len(videos))
            await asyncio.sleep(15)

    async def analysis_loop(self) -> None:
        while True:
            video = await self.analysis_queue.get()
            try:
                result = await self.analyzer.analyze(video)
                if result.risk_score > 0.7:
                    case = self._flag_for_analyst(result)
                    log.info("⚑ Флаг аналитику: %s risk=%.2f → %s",
                             result.account.get("handle"), result.risk_score, case["case_id"])
            finally:
                self.analysis_queue.task_done()

    async def prediction_loop(self) -> None:
        while True:
            accounts = await self.collector.recent_accounts(max_age_days=30)
            for acc in accounts:
                pred = self.predictor.score(acc)
                if pred >= 0.6:
                    enriched = {**acc, "caption": acc.get("bio", "")}
                    await self.analysis_queue.put({"account": enriched, "predicted": pred})
                    log.info("Предиктор: @%s упреждающе в очередь (pred=%.2f)",
                             acc.get("handle"), pred)
            await asyncio.sleep(300)  # 5 мин

    async def network_update_loop(self) -> None:
        while True:
            await asyncio.sleep(1800)  # 30 мин
            central = self.network_mapper.get_central_accounts(3)
            log.info("Граф обновлён: %d узлов, центр: %s",
                     len(self.network_mapper.graph),
                     ", ".join(c["handle"] for c in central) or "—")

    # ── флаг + решения аналитика ──
    def _next_case_id(self) -> str:
        self._case_seq += 1
        return f"CASE-{self._case_seq}"

    def _flag_for_analyst(self, result) -> dict:
        case_id = self._next_case_id()
        acc = result.account
        case = {
            "case_id": case_id,
            "created_at": datetime.now(timezone.utc),
            "analyst_name": None,
            "status": "awaiting_analyst",
            "account": {
                "handle": acc.get("handle"),
                "platform": acc.get("platform"),
                "url": acc.get("url", f"https://{acc.get('platform','')}.com/@{acc.get('handle')}"),
                "bio": acc.get("bio", acc.get("bio_text", "")),
            },
            "risk_score": result.risk_score,
            "violation_class": result.violation_class,
            "evidence": list(result.evidence),
            "probe_result": None,
            "network_connections": self.network_mapper.find_connections(acc),
        }
        self.cases[case_id] = case
        self.flagged[case_id] = case
        return case

    async def handle_analyst_decision(self, case_id: str, decision: str, analyst: str):
        case = self.cases.get(case_id)
        if case is None:
            raise KeyError(f"Дело не найдено: {case_id}")
        case["analyst_name"] = analyst

        if decision == "approve_probe":
            account = {
                "platform": case["account"]["platform"],
                "handle": case["account"]["handle"],
                "bio_url": case["account"].get("url"),
                "bio_text": case["account"].get("bio", ""),
            }
            probe = await self.probe_agent.probe(account, approved_by=analyst)
            case["probe_result"] = probe.to_dict() if hasattr(probe, "to_dict") else probe
            case["status"] = "probed"
            self.flagged.pop(case_id, None)
            return {"status": "probed", "case_id": case_id, "probe_result": case["probe_result"]}

        if decision == "approve_report":
            docx_bytes = self.report_gen.generate(case)
            case["status"] = "report_generated"
            self.flagged.pop(case_id, None)
            return {"status": "report_generated", "case_id": case_id, "docx": docx_bytes}

        if decision == "reject":
            case["status"] = "rejected"
            self.flagged.pop(case_id, None)
            return {"status": "rejected", "case_id": case_id}

        if decision == "escalate":
            case["status"] = "escalated"
            return {"status": "escalated", "case_id": case_id}

        raise ValueError(f"Неизвестное решение: {decision}")


# ════════════════════════ FastAPI ════════════════════════

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import Response  # noqa: E402
from pydantic import BaseModel  # noqa: E402

orchestrator = SunkarOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # засеять граф демо-аккаунтами, чтобы эндпоинты сети были полезны сразу
    for acc in globals().get("_DEMO_ACCOUNTS", []):
        orchestrator.network_mapper.add_account(acc)
    task = asyncio.create_task(orchestrator.run_pipeline())
    log.info("СУНКАР online")
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass


app = FastAPI(title="СУНКАР · Orchestrator", version="1.0.0", lifespan=lifespan)


class DecisionRequest(BaseModel):
    case_id: str
    decision: str  # approve_probe | approve_report | reject | escalate
    analyst: str


@app.get("/network/graph")
async def network_graph():
    return orchestrator.network_mapper.to_graph_json()


@app.get("/network/central")
async def network_central(top_n: int = 3):
    return {"central_accounts": orchestrator.network_mapper.get_central_accounts(top_n)}


@app.post("/network/find-connections/{handle}")
async def network_find_connections(handle: str):
    handle = handle.lstrip("@")
    node = orchestrator.network_mapper.graph.get(handle)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Аккаунт не найден в графе: {handle}")
    return {"handle": handle, "connections": orchestrator.network_mapper.find_connections(node["metadata"])}


@app.get("/cases/flagged")
async def flagged_cases():
    return {"flagged": [
        {"case_id": c["case_id"], "handle": c["account"]["handle"],
         "risk_score": c["risk_score"], "status": c["status"]}
        for c in orchestrator.flagged.values()
    ]}


@app.post("/analyst/decision")
async def analyst_decision(body: DecisionRequest):
    try:
        result = await orchestrator.handle_analyst_decision(body.case_id, body.decision, body.analyst)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # approve_report → отдать DOCX файлом
    if isinstance(result, dict) and "docx" in result:
        return Response(
            content=result["docx"],
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="AFM_report_{body.case_id}.docx"'},
        )
    return result


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "nodes": len(orchestrator.network_mapper.graph),
        "queue": orchestrator.analysis_queue.qsize(),
        "flagged": len(orchestrator.flagged),
    }
