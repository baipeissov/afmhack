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

from fastapi import FastAPI, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.dossier import build_dossier  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "risk_queue.jsonl"
REPORTS_PATH = ROOT / "data" / "citizen_reports.jsonl"
DECISIONS_PATH = ROOT / "data" / "analyst_decisions.jsonl"
INCOMING_DIR = ROOT / "data" / "incoming"

app = FastAPI(title="AI Media Watch")

# Next.js dev server (localhost:3000) дёргает этот API из браузера (для
# /analyze и /queue/decision) — без CORS браузер такие запросы заблокирует.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReportIn(BaseModel):
    url: str | None = None
    note: str | None = None
    reporter_contact: str | None = None


class DecisionIn(BaseModel):
    item_id: str
    decision: str  # "approve" | "reject" | "request_review"
    analyst_comment: str | None = None


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
        "recommendation": dossier["recommendation"],
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
    return {"status": "recorded"}


@app.post("/analyze")
async def analyze(
    file: UploadFile,
    account_handle: str | None = Form(None),
    platform: str = Form("TikTok"),
    account_age_days: float = Form(365),
    follower_growth: float = Form(0.0),
    referral_link_in_bio: bool = Form(False),
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
    dossier = build_dossier(str(dest), account_metadata)

    item_id = f"manual_{uuid.uuid4().hex[:8]}"
    record = _dossier_to_queue_record(dossier, item_id, source="manual_upload", account_handle=account_handle, platform=platform)

    items = _read_queue()
    items.append(record)
    _write_queue(items)

    return record


@app.get("/")
def root():
    return {"service": "AI Media Watch", "endpoints": ["/report", "/queue", "/queue/{id}", "/queue/decision", "/analyze"]}
