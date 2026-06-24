# Probe Agent — агент-зондировщик доказательной базы (АФМ)

Собирает доказательства с **публичных** ресурсов проверяемого аккаунта после
**ручного одобрения аналитиком**. Все действия пишутся в `audit_log.jsonl`.

## Установка

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium                              # для скриншотов
```

## Запуск

```bash
export ANALYST_SECRET="super-secret"          # PowerShell: $env:ANALYST_SECRET="super-secret"
uvicorn backend.probe_agent:app --reload --port 8000
```

## Вызов

```bash
curl -X POST http://localhost:8000/probe \
  -H "Content-Type: application/json" \
  -H "X-Analyst-Token: super-secret" \
  -d '{"account_id": "acc_easy_earn_kz", "analyst_name": "Айгерим Н."}'
```

Ответ: `{ "result": {...}, "evidence_report": {...} }` — где `evidence_report`
готов к вставке в рапорт АФМ.

## Правовые ограничения

- Только публичный URL из bio. Никакого обхода авторизации, капчи или paywall.
- Доступ к приватным данным не выполняется.
- Скриншоты хранятся в `evidence/`, целостность — через SHA256.
- `evidence/` и `audit_log.jsonl` исключены из git.

## Использование класса напрямую

```python
import asyncio
from backend.probe_agent import ProbeAgent

agent = ProbeAgent()
account = {"platform": "tiktok", "handle": "easy_earn_kz",
           "bio_url": "https://example.com/x", "bio_text": "доход 30% t.me/quick_profit_kz"}
result = asyncio.run(agent.probe(account, approved_by="Аналитик"))
print(result.to_evidence_dict())
```
