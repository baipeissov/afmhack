"""
FastAPI-сервис. Эндпоинты:
  POST /report         - жалоба гражданина (url/файл) -> попадает в очередь Collector'а
  GET  /queue          - risk-очередь (risk_queue.jsonl), отсортированная по risk_score
  GET  /queue/{id}     - полное досье одного кейса (для карточки в дашборде)
  POST /queue/decision - решение аналитика (approve/reject/request_review)
  POST /analyze        - ручной запуск анализа конкретного файла (загрузка из дашборда
                          для теста/демо без поднятого Collector'а; в проде анализ
                          запускает Collector автоматически, см. scripts/run_collector.py)

Human-in-the-loop: только /queue/decision продвигает кейс дальше — система
сама ничего не отправляет в органы.
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.dossier import build_dossier  # noqa: E402
from pipeline import live_stream, url_fetch  # noqa: E402
from pipeline.network_builder import build_network  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "risk_queue.jsonl"
REPORTS_PATH = ROOT / "data" / "citizen_reports.jsonl"
DECISIONS_PATH = ROOT / "data" / "analyst_decisions.jsonl"
INCOMING_DIR = ROOT / "data" / "incoming"

app = FastAPI(title="AI Media Watch")

# Next.js dev server дёргает этот API из браузера (для /analyze,
# /queue/decision, /network) — без CORS браузер такие запросы заблокирует.
# 3001 разрешён вторым: порт 3000 на этой машине может быть занят другим
# проектом, и тогда дашборд поднимается на 3001.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Агентный слой (СУНКАР): discovery / специалисты / датасет / граф / следователь /
# связной с АФМ. См. agents/routes.py.
from agents.routes import router as agents_router  # noqa: E402

app.include_router(agents_router)


@app.on_event("startup")
async def _maybe_start_orchestrator():
    """Фоновые циклы скрейпинга/анализа запускаем только по флагу окружения,
    чтобы dev-запуск API не начинал автоматически качать видео."""
    import os

    if os.getenv("SUNKAR_ORCHESTRATOR", "false").lower() == "true":
        import asyncio

        from agents.orchestrator import orchestrator
        asyncio.create_task(orchestrator.run())


class ReportIn(BaseModel):
    url: str | None = None
    note: str | None = None
    reporter_contact: str | None = None


class DecisionIn(BaseModel):
    item_id: str
    decision: str  # "approve" | "reject" | "request_review"
    analyst_comment: str | None = None


class AnalyzeUrlIn(BaseModel):
    url: str
    # Возраст аккаунта/рост подписчиков НЕ доступны через yt-dlp (закрытые
    # метрики платформы, нужен TikTok Research API / Instagram Graph API
    # с одобренным доступом, см. pipeline/metadata.py) — поэтому остаются
    # опциональными ручными полями "точнее, если знаешь", а не блокером.
    account_age_days: float | None = None
    follower_growth: float | None = None
    referral_link_in_bio: bool = False


def _read_queue() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    items = []
    for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


def _write_queue(items: list[dict]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _dossier_to_queue_record(dossier: dict, item_id: str, source: str, account_handle: str | None, platform: str) -> dict:
    """Сплющивает полное досье в запись очереди — фронту нужны и сводные
    поля для списка (handle/severity/modalities), и полное досье для
    карточки кейса, поэтому храним всё в одной записи."""
    raw = dossier["raw"]
    return {
        "item_id": item_id,
        "source": source,
        "account_handle": account_handle or "unknown",
        "platform": platform,
        "video_path": dossier["video_path"],
        "risk_score": dossier["risk_score"],
        "risk_level": dossier["risk_level"],
        "top_class": dossier["top_class"],
        "top_class_ru": dossier["top_class_ru"],
        "contributions": dossier["contributions"],
        "explanations": dossier["explanations"],
        "llm_explanations": dossier.get("llm_explanations", []),
        "recommendation": dossier["recommendation"],
        "entities": dossier.get("entities", {}),
        "modalities": {
            "asr": len(raw["transcript"]) > 0,
            "ocr": len(raw["ocr"]) > 0,
            "vision": len(raw["visual"]) > 0,
        },
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending_review",
        "analyst_comment": None,
    }


@app.post("/report")
def submit_report(report: ReportIn):
    """Жалоба гражданина. Подбирается коннектором citizen_reports.py на
    следующем цикле опроса Collector'а — никакого ручного "анализируй сейчас"."""
    REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    report_id = str(uuid.uuid4())[:8]
    with open(REPORTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"report_id": report_id, **report.model_dump()}, ensure_ascii=False) + "\n")
    return {"status": "queued", "report_id": report_id}


@app.get("/queue")
def get_queue():
    items = _read_queue()
    items.sort(key=lambda x: x.get("risk_score") or 0, reverse=True)
    return items


@app.get("/queue/{item_id}")
def get_queue_item(item_id: str):
    for item in _read_queue():
        if item["item_id"] == item_id:
            return item
    return {"error": "not_found"}


@app.get("/network")
def get_network():
    """Граф связей аккаунтов по общим сигналам (Telegram-канал, реф-ссылка,
    хэштег, номер Kaspi), извлечённым из видео в очереди — см.
    pipeline/entity_extractor.py + pipeline/network_builder.py."""
    return build_network(_read_queue())


@app.post("/queue/decision")
def record_decision(decision: DecisionIn):
    """Human-in-the-loop: аналитик подтверждает/отклоняет кейс. Это
    единственное действие, которое продвигает кейс дальше — система сама
    ничего не отправляет в органы."""
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DECISIONS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(decision.model_dump(), ensure_ascii=False) + "\n")

    items = _read_queue()
    for item in items:
        if item["item_id"] == decision.item_id:
            item["status"] = decision.decision
            item["analyst_comment"] = decision.analyst_comment
    _write_queue(items)

    # Цикл самообучения: подтверждённый кейс пополняет обучающий датасет
    # (только approve, только подтверждённые человеком данные).
    curated = None
    if decision.decision == "approve":
        try:
            from agents.dataset.curator import DatasetCuratorAgent

            curated = DatasetCuratorAgent().curate_case(decision.item_id)
        except Exception as e:  # noqa: BLE001
            curated = {"ok": False, "error": str(e)}
    return {"status": "recorded", "curated": curated}


@app.post("/analyze")
async def analyze(
    file: UploadFile,
    account_handle: str | None = Form(None),
    platform: str = Form("TikTok"),
    account_age_days: float = Form(365),
    follower_growth: float = Form(0.0),
    referral_link_in_bio: bool = Form(False),
    caption: str | None = Form(None),
):
    """Загрузка файла из дашборда (или curl) -> полный анализ -> результат
    сразу попадает в /queue, чтобы дашборд показал его в списке без
    дополнительных действий."""
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    dest = INCOMING_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())

    account_metadata = {
        "account_age_days": account_age_days,
        "follower_growth": follower_growth,
        "referral_link_in_bio": referral_link_in_bio,
    }
    dossier = build_dossier(str(dest), account_metadata, caption=caption)

    item_id = f"manual_{uuid.uuid4().hex[:8]}"
    record = _dossier_to_queue_record(dossier, item_id, source="manual_upload", account_handle=account_handle, platform=platform)

    items = _read_queue()
    items.append(record)
    _write_queue(items)

    return record


@app.post("/analyze/url")
def analyze_url(payload: AnalyzeUrlIn):
    """Аналитик вставляет только URL — видео скачивается и caption/@handle
    извлекаются автоматически через yt-dlp (pipeline/url_fetch.py), без
    ручного ввода. Возраст аккаунта/рост подписчиков остаются опциональными
    (платформы их не отдают анонимно) — по умолчанию берутся нейтральные
    значения из pipeline/metadata.DEFAULTS."""
    try:
        fetched = url_fetch.fetch_video(payload.url, INCOMING_DIR)
    except Exception as e:  # noqa: BLE001 — приватный/удалённый пост, неподдерживаемая ссылка и т.п.
        return {"error": "fetch_failed", "detail": str(e)}

    account_metadata = {}
    if payload.account_age_days is not None:
        account_metadata["account_age_days"] = payload.account_age_days
    if payload.follower_growth is not None:
        account_metadata["follower_growth"] = payload.follower_growth
    account_metadata["referral_link_in_bio"] = payload.referral_link_in_bio

    dossier = build_dossier(fetched["local_path"], account_metadata, caption=fetched["caption"])

    item_id = f"url_{uuid.uuid4().hex[:8]}"
    record = _dossier_to_queue_record(
        dossier, item_id, source="url_fetch",
        account_handle=fetched["account_handle"], platform=fetched["platform"],
    )
    record["source_url"] = payload.url

    items = _read_queue()
    items.append(record)
    _write_queue(items)

    return record


def _run_live_analysis(video_path: str, session_id: str, account_handle: str | None, platform: str, chunk_seconds: int) -> None:
    """Выполняется в фоне (BackgroundTasks): режет видео на чанки и
    пишет в очередь результат по каждому чанку сразу, как он готов — клиент
    видит частичные результаты в /queue по мере анализа, не дожидаясь
    последнего чанка."""
    for result in live_stream.analyze_chunks(video_path):
        item_id = f"{session_id}_chunk{result['chunk_index']:03d}"
        record = _dossier_to_queue_record(
            result["dossier"], item_id, source="live_stream", account_handle=account_handle, platform=platform
        )
        record["stream_offset_seconds"] = result["stream_offset_seconds"]
        record["live_session_id"] = session_id

        items = _read_queue()
        items.append(record)
        _write_queue(items)


@app.post("/analyze/live")
async def analyze_live(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    account_handle: str | None = Form(None),
    platform: str = Form("TikTok"),
    chunk_seconds: int = Form(live_stream.DEFAULT_CHUNK_SECONDS),
):
    """Имитация прямого эфира: видео режется на чанки по chunk_seconds и
    анализируется по мере готовности — каждый чанк появляется в /queue
    отдельной записью с live_session_id, не дожидаясь конца всего видео.
    (Реальный живой HLS-захват — pipeline/live_stream.capture_live_chunks —
    не используется здесь намеренно, см. docstring модуля.)"""
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    dest = INCOMING_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())

    session_id = f"live_{uuid.uuid4().hex[:8]}"
    background_tasks.add_task(_run_live_analysis, str(dest), session_id, account_handle, platform, chunk_seconds)
    return {"status": "started", "live_session_id": session_id}


@app.get("/")
def root():
    return {
        "service": "AI Media Watch",
        "endpoints": ["/report", "/queue", "/queue/{id}", "/queue/decision", "/analyze", "/analyze/url", "/analyze/live", "/network"],
    }
