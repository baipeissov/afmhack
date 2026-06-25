"""
Демо мультиагентной системы СУНКАР без живого скрейпинга/тяжёлого ML.

Прогоняет весь флоу на засеянном кейсе:
  специалист → флаг → подтверждение аналитика → пополнение датасета →
  граф связей → следователь (симуляция переписки) → связной с АФМ (ответ + DOCX).

Запуск:
  python scripts/run_demo_agents.py
Нужен OPENROUTER_API_KEY в .env (иначе агенты деградируют до правил/шаблонов).
"""

from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agents.base as base  # noqa: E402

# Засеваем временную risk-очередь демо-кейсом (не трогаем рабочий risk_queue.jsonl).
CID = "DEMO-" + uuid.uuid4().hex[:6]
_tmp = Path(tempfile.gettempdir()) / "sunkar_demo_queue.jsonl"
_case = {
    "item_id": CID, "account_handle": "easy_earn_kz", "platform": "TikTok",
    "url": "https://tiktok.com/@easy_earn_kz", "followers": 145000, "discovered_at": "2026-06-01",
    "top_class": "pyramid_investment", "top_class_ru": "гарантированный доход / пирамида",
    "risk_score": 0.91, "risk_level": "HIGH",
    "caption": "Удвоим депозит за неделю! Гарантия 200%. Пиши t.me/quick_profit_kz #инвестиции",
    "explanations": ["🔴 [00:03] Аудио: \"гарантированный доход 200%\" → пирамида (p=0.94)"],
    "recommendation": "Приоритетная проверка",
    "raw": {"transcript": [{"start": 3, "end": 6, "text": "гарантированный доход 200 процентов за неделю"}],
            "ocr": [{"frame_time": 4, "text": "+847 000 тенге за 3 дня"}],
            "visual": [{"frame_time": 2, "scores": {"fake_income_screenshot": 0.34}}]},
}
_tmp.write_text(json.dumps(_case, ensure_ascii=False) + "\n", encoding="utf-8")
base.RISK_QUEUE = _tmp

from agents.dataset.curator import DatasetCuratorAgent  # noqa: E402
from agents.engagement.engagement_agent import EngagementAgent  # noqa: E402
from agents.liaison.liaison_agent import LiaisonAgent  # noqa: E402
from agents.network import NetworkMapper  # noqa: E402
from agents.specialists.router import SpecialistRouter  # noqa: E402


def hr(t):
    print("\n" + "=" * 70 + f"\n {t}\n" + "=" * 70)


def main():
    print(f"Демо-кейс: {CID}  (@{_case['account_handle']}, риск {_case['risk_score']})")

    hr("1. СПЕЦ-АГЕНТ по типу мошенничества")
    verdict = SpecialistRouter().run(CID)
    print("Специалист:", verdict.get("display_ru"))
    print("Подтверждено:", verdict.get("confirmed"), "| уверенность:", verdict.get("confidence"),
          "| LLM:", verdict.get("llm_used"))
    print("Обоснование:", verdict.get("rationale"))

    hr("2. ПОДТВЕРЖДЕНИЕ → ПОПОЛНЕНИЕ ДАТАСЕТА (цикл самообучения)")
    cur = DatasetCuratorAgent().curate_case(CID)
    print("Куратор:", cur)

    hr("3. ГРАФ СВЯЗЕЙ")
    nm = NetworkMapper()
    nm.add_account({"handle": "easy_earn_kz", "caption": _case["caption"], "platform": "tiktok",
                    "risk_score": 0.91, "violation_class": "pyramid_investment"})
    nm.add_account({"handle": "casino_win_astana", "caption": "Бонус! t.me/quick_profit_kz #инвестиции",
                    "platform": "instagram", "risk_score": 0.88, "violation_class": "casino_betting"})
    print("Узлов:", len(nm.graph), "| связей:", len(nm.to_graph_json()["links"]))
    print("Центральные:", [c["handle"] for c in nm.get_central_accounts(2)])

    hr("4. СЛЕДОВАТЕЛЬ (симуляция переписки, под одобрение человека)")
    eng = EngagementAgent()
    s = eng.start(CID)
    print("Легенда:", s["convo"]["persona"].get("name"))
    print("Черновик 1-го сообщения:", s["convo"]["pending_draft"]["text"][:140])
    r = eng.approve_and_send(CID, analyst="Демо-Аналитик")
    print("→ Ответ 'мошенника' (симуляция):", (r.get("reply") or "")[:220])
    summ = eng.summarize(CID)
    print("Сведённые улики:", str(summ.get("intelligence", {}).get("summary", ""))[:200])

    hr("5. СВЯЗНОЙ С АФМ (диалог + рапорт)")
    la = LiaisonAgent()
    ans = la.chat(CID, "Кратко: почему высокий риск и что рекомендуете?")
    print("Ответ связного:", str(ans.get("answer"))[:280])
    rep = la.generate_report(CID, analyst="Демо-Аналитик", out_dir=Path(tempfile.gettempdir()) / "sunkar_reports")
    print("Рапорт DOCX:", rep)

    hr("ГОТОВО")
    print("Весь мультиагентный цикл отработал. Для живого скрейпинга/анализа нужен ML-стек и uvicorn api.main.")


if __name__ == "__main__":
    main()
