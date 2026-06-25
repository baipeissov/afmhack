"""
FastAPI-роутер агентного слоя. Подключается в api/main.py через
app.include_router(agents_router). Все агенты доступны через синглтон
orchestrator (общий граф и состояние).
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .base import DATA_DIR
from .llm import default_client
from .orchestrator import orchestrator

log = logging.getLogger("sunkar.routes")
router = APIRouter(tags=["agents"])


# ───────────────── модели запросов ─────────────────
class CurateIn(BaseModel):
    item_id: str
    label_override: str | None = None


class EngagementSendIn(BaseModel):
    analyst: str
    edited_text: str | None = None


class ChatIn(BaseModel):
    question: str
    history: list[dict] | None = None


class ReportIn(BaseModel):
    analyst: str


# ───────────────── здоровье / LLM ─────────────────
@router.get("/agents/health")
def agents_health():
    return {
        "status": "ok",
        "llm_available": default_client.available,
        "llm_models": default_client.models[:3],
        "network_nodes": len(orchestrator.network.graph),
        "dataset": orchestrator.curator.stats(),
    }


# ───────────────── discovery / analysis ─────────────────
@router.post("/discovery/run")
def discovery_run():
    """Один цикл гибридного скрейпинга → анализ → запись в risk_queue.
    Требует ML-стек (build_dossier) на хосте."""
    return orchestrator.cycle_once()


# ───────────────── спец-агенты ─────────────────
@router.post("/specialists/run/{item_id}")
def specialists_run(item_id: str):
    verdict = orchestrator.specialists.run(item_id)
    if verdict is None:
        raise HTTPException(404, f"Кейс не найден: {item_id}")
    return verdict


# ───────────────── датасет / переобучение ─────────────────
@router.post("/dataset/curate")
def dataset_curate(body: CurateIn):
    return orchestrator.curator.curate_case(body.item_id, body.label_override)


@router.get("/dataset/stats")
def dataset_stats():
    return orchestrator.curator.stats()


@router.post("/retrain")
def retrain():
    """Пересобрать датасет (с Layer 4) и переобучить Component A. Тяжёлый шаг."""
    return orchestrator.retrainer.retrain()


# ───────────────── граф связей ─────────────────
@router.get("/network/graph")
def network_graph():
    return orchestrator.network.to_graph_json()


@router.get("/network/central")
def network_central(top_n: int = 3):
    return {"central_accounts": orchestrator.network.get_central_accounts(top_n)}


@router.post("/network/find-connections/{handle}")
def network_connections(handle: str):
    handle = handle.lstrip("@")
    node = orchestrator.network.graph.get(handle)
    if node is None:
        raise HTTPException(404, f"Аккаунт не найден в графе: {handle}")
    return {"handle": handle, "connections": orchestrator.network.find_connections(node["metadata"])}


# ───────────────── следователь (engagement) ─────────────────
@router.post("/engagement/{item_id}/start")
def engagement_start(item_id: str):
    res = orchestrator.engagement.start(item_id)
    if not res.get("ok"):
        raise HTTPException(409 if res.get("reason") == "already_started" else 404, res.get("reason"))
    return res


@router.post("/engagement/{item_id}/draft-next")
def engagement_draft(item_id: str):
    return orchestrator.engagement.draft_next(item_id)


@router.post("/engagement/{item_id}/approve")
def engagement_approve(item_id: str, body: EngagementSendIn):
    return orchestrator.engagement.approve_and_send(item_id, body.analyst, body.edited_text)


@router.post("/engagement/{item_id}/reject")
def engagement_reject(item_id: str, body: EngagementSendIn):
    return orchestrator.engagement.reject_draft(item_id, body.analyst)


@router.get("/engagement/{item_id}")
def engagement_get(item_id: str):
    convo = orchestrator.engagement.conversation(item_id)
    if convo is None:
        raise HTTPException(404, "Переписка не начата")
    return convo


@router.post("/engagement/{item_id}/summarize")
def engagement_summarize(item_id: str):
    return orchestrator.engagement.summarize(item_id)


# ───────────────── связной с АФМ (liaison) ─────────────────
@router.post("/liaison/{item_id}/chat")
def liaison_chat(item_id: str, body: ChatIn):
    res = orchestrator.liaison.chat(item_id, body.question, body.history)
    if not res.get("ok"):
        raise HTTPException(404, res.get("reason"))
    return res


@router.post("/liaison/{item_id}/report")
def liaison_report(item_id: str, body: ReportIn):
    res = orchestrator.liaison.generate_report(item_id, body.analyst)
    if not res.get("ok"):
        raise HTTPException(400, res.get("reason"))
    path = Path(res["path"])
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )
