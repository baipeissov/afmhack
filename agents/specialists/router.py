"""
SpecialistRouter — диспетчер: выбирает спец-агента по top_class кейса
(Component A) и запускает углублённый разбор. Результат пишется в
case["specialist"] и (опц.) корректирует risk_score.
"""

from __future__ import annotations

import logging

from ..base import Agent, get_case, update_case
from .specialists import ALL_SPECIALISTS

log = logging.getLogger("sunkar.specialists.router")


class SpecialistRouter(Agent):
    name = "specialist_router"

    def __init__(self) -> None:
        self._by_class = {cls.violation_class: cls() for cls in ALL_SPECIALISTS}

    def specialist_for(self, top_class: str):
        return self._by_class.get(top_class)

    def run(self, item_id: str, apply_risk_adjust: bool = True) -> dict | None:
        """Запускает спец-агента по классу кейса. Возвращает вердикт специалиста."""
        case = get_case(item_id)
        if case is None:
            return None
        top_class = case.get("top_class", "clean")
        specialist = self.specialist_for(top_class)
        if specialist is None:
            # clean или неизвестный класс — специалиста нет
            return {"specialist": None, "reason": f"no_specialist_for_{top_class}"}

        verdict = specialist.analyze(case)

        patch = {"specialist": verdict}
        if apply_risk_adjust and verdict.get("risk_adjust"):
            new_risk = max(0.0, min(1.0, float(case.get("risk_score", 0.0)) + verdict["risk_adjust"]))
            patch["risk_score"] = round(new_risk, 4)
        update_case(item_id, patch)
        self.log_action("routed", item_id=item_id, top_class=top_class,
                        confirmed=verdict.get("confirmed"))
        return verdict
