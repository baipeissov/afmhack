"""
probe_agent.py — Агент-зондировщик доказательной базы для АФМ.

Назначение
----------
После того как аналитик ВРУЧНУЮ одобряет проверку, агент собирает доказательную
базу с ПУБЛИЧНО доступных ресурсов проверяемого аккаунта (ссылка из bio и её
содержимое). Фиксирует обещания доходности, контакты, Telegram-каналы и делает
скриншот-доказательство с хэшем SHA256 для приобщения к рапорту.

Правовые ограничения (соблюдаются в коде)
-----------------------------------------
* Агент работает ТОЛЬКО с публичным URL из bio аккаунта.
* НИКАКОГО обхода авторизации, капчи, paywall или доступа к приватным данным.
* Запрос выполняется обычным GET как у рядового пользователя браузера.
* Любое действие (старт, кто одобрил, какой аккаунт, результат) пишется в
  неизменяемый журнал аудита audit_log.jsonl.

Запуск API
----------
    pip install -r requirements.txt
    playwright install chromium          # один раз, для скриншотов
    export ANALYST_SECRET="<секрет>"     # Windows PowerShell: $env:ANALYST_SECRET="..."
    uvicorn backend.probe_agent:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ───────────────────────────── конфигурация ─────────────────────────────

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "ru,ru-RU;q=0.9,en;q=0.8",
}
REQUEST_TIMEOUT = 10  # сек

EVIDENCE_DIR = Path(os.getenv("PROBE_EVIDENCE_DIR", "evidence"))
AUDIT_LOG = Path(os.getenv("PROBE_AUDIT_LOG", "audit_log.jsonl"))

# ───────────────────────────── паттерны ─────────────────────────────

# обещания доходности: «30%», «до 25,5 %» и т.п.
PERCENT_RE = re.compile(r"\d+[.,]?\d*\s*%")

# маркеры финансовой манипуляции
RISK_KEYWORDS = [
    "гарант",        # гарантия / гарантируем
    "депозит",
    "вывод",
    "реферал",
    "пригласи",
    "пассивный доход",
    "без риска",
    "доход",
    "прибыл",        # прибыль / прибыльный
    "инвестиц",
    "удвоен",        # удвоим
    "x2", "x3", "х2", "х3",
]

# контакты
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# телефоны KZ/RU: +7 / 8 (XXX) XXX-XX-XX и вариации
PHONE_RE = re.compile(
    r"(?:\+?7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
)
# Telegram-ссылки и юзернеймы
TELEGRAM_RE = re.compile(
    r"(?:https?://)?(?:t\.me|telegram\.me|telegram\.dog)/[A-Za-z0-9_+/]+",
    re.IGNORECASE,
)


# ───────────────────────────── результат ─────────────────────────────

@dataclass
class ProbeResult:
    account_handle: str
    probed_at: datetime
    approved_by: str
    bio_url: Optional[str]
    landing_page_title: Optional[str]
    extracted_promises: list[str] = field(default_factory=list)   # обещания дохода
    extracted_contacts: list[str] = field(default_factory=list)   # телефоны, email
    telegram_links: list[str] = field(default_factory=list)
    screenshot_path: Optional[str] = None
    screenshot_sha256: Optional[str] = None
    additional_risk_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Полная сериализация (даты → ISO 8601)."""
        d = asdict(self)
        d["probed_at"] = self.probed_at.astimezone(timezone.utc).isoformat()
        return d

    def to_evidence_dict(self) -> dict:
        """Форматирует результат для вставки в рапорт АФМ."""
        return {
            "субъект_проверки": f"@{self.account_handle}",
            "дата_проверки_utc": self.probed_at.astimezone(timezone.utc).isoformat(),
            "одобрено_аналитиком": self.approved_by,
            "источник": {
                "ссылка_из_bio": self.bio_url,
                "заголовок_лендинга": self.landing_page_title,
                "доступ": "публичный URL, без обхода авторизации",
            },
            "обнаруженные_обещания_дохода": self.extracted_promises,
            "контактные_данные": self.extracted_contacts,
            "telegram_каналы": self.telegram_links,
            "скриншот_доказательство": {
                "путь": self.screenshot_path,
                "sha256": self.screenshot_sha256,
                "примечание": (
                    "Целостность подтверждается хэшем SHA256. Любое изменение "
                    "файла изменит хэш."
                ),
            },
            "дополнительные_сигналы_риска": self.additional_risk_signals,
            "методологическая_оговорка": (
                "Все данные получены с публично доступного ресурса, указанного "
                "самим субъектом в bio. Сбор выполнен после ручного одобрения "
                "аналитика и зафиксирован в журнале аудита."
            ),
        }


# ───────────────────────────── агент ─────────────────────────────

class ProbeAgent:
    def __init__(
        self,
        evidence_dir: Path = EVIDENCE_DIR,
        audit_log: Path = AUDIT_LOG,
    ) -> None:
        self.evidence_dir = Path(evidence_dir)
        self.audit_log = Path(audit_log)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)

    # ── публичный API ──────────────────────────────────────────────
    async def probe(self, account: dict, approved_by: str) -> ProbeResult:
        handle = account.get("handle", "unknown").lstrip("@")
        bio_url = account.get("bio_url")
        bio_text = account.get("bio_text") or ""
        probed_at = datetime.now(timezone.utc)
        ts = probed_at.strftime("%Y%m%dT%H%M%SZ")

        # 1. аудит: старт
        self._audit(
            event="probe_started",
            handle=handle,
            platform=account.get("platform"),
            approved_by=approved_by,
            bio_url=bio_url,
            timestamp=probed_at.isoformat(),
        )

        result = ProbeResult(
            account_handle=handle,
            probed_at=probed_at,
            approved_by=approved_by,
            bio_url=bio_url,
            landing_page_title=None,
        )

        # тексты, по которым ищем сигналы: bio + содержимое лендинга
        corpus = [bio_text]

        # 2. если есть публичная ссылка из bio — разбираем её
        if bio_url:
            try:
                # сетевой ввод-вывод в отдельном потоке, чтобы не блокировать loop
                title, description, page_text = await asyncio.to_thread(
                    self._fetch_landing, bio_url
                )
                result.landing_page_title = title
                corpus.extend([title or "", description or "", page_text or ""])
                result.additional_risk_signals.append("Лендинг из bio успешно получен")
            except Exception as exc:  # noqa: BLE001 — фиксируем как сигнал, не падаем
                result.additional_risk_signals.append(
                    f"Лендинг недоступен или таймаут: {type(exc).__name__}"
                )
                self._audit(
                    event="landing_fetch_failed",
                    handle=handle,
                    bio_url=bio_url,
                    error=f"{type(exc).__name__}: {exc}",
                )

            # 2d/2e: скриншот-доказательство + хэш
            shot_path = await self._screenshot(bio_url, handle, ts)
            if shot_path:
                result.screenshot_path = str(shot_path)
                result.screenshot_sha256 = self._sha256(shot_path)
                result.additional_risk_signals.append(
                    "Скриншот-доказательство зафиксирован (SHA256)"
                )
            else:
                result.additional_risk_signals.append(
                    "Скриншот не получен (playwright недоступен или ошибка рендера)"
                )

        joined = "\n".join(corpus)

        # 2c: извлечение паттернов
        result.extracted_promises = self._extract_promises(joined)
        result.extracted_contacts = self._extract_contacts(joined)

        # 3: Telegram-ссылки из bio_text + контента лендинга
        result.telegram_links = self._extract_telegram(joined)

        # производные сигналы риска
        result.additional_risk_signals.extend(self._derive_signals(joined, result))
        # убрать дубликаты, сохранив порядок
        result.additional_risk_signals = _dedup(result.additional_risk_signals)

        # аудит: финал
        self._audit(
            event="probe_completed",
            handle=handle,
            approved_by=approved_by,
            promises=len(result.extracted_promises),
            contacts=len(result.extracted_contacts),
            telegram_links=len(result.telegram_links),
            screenshot_sha256=result.screenshot_sha256,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return result

    # ── сбор лендинга (синхронно, вызывается в потоке) ─────────────
    def _fetch_landing(self, url: str) -> tuple[Optional[str], Optional[str], str]:
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=HTTP_HEADERS,
            allow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else None

        description = None
        meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if meta and meta.get("content"):
            description = meta["content"].strip()

        # видимый текст без скриптов/стилей
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        page_text = soup.get_text(separator=" ", strip=True)
        return title, description, page_text

    # ── извлечение паттернов ───────────────────────────────────────
    @staticmethod
    def _extract_promises(text: str) -> list[str]:
        promises: list[str] = []
        # проценты доходности
        promises.extend(m.group(0).strip() for m in PERCENT_RE.finditer(text))
        # фразы с финансовыми обещаниями
        for line in re.split(r"[\n\.!?;•]", text):
            low = line.lower()
            if any(k in low for k in ("доход", "прибыл", "удвоен", "пассивн", "без риска")):
                cleaned = line.strip()
                if 3 < len(cleaned) < 200:
                    promises.append(cleaned)
        return _dedup(promises)

    @staticmethod
    def _extract_contacts(text: str) -> list[str]:
        contacts: list[str] = []
        contacts.extend(m.group(0) for m in EMAIL_RE.finditer(text))
        contacts.extend(re.sub(r"\s+", " ", m.group(0)).strip() for m in PHONE_RE.finditer(text))
        return _dedup(contacts)

    @staticmethod
    def _extract_telegram(text: str) -> list[str]:
        links = []
        for m in TELEGRAM_RE.finditer(text):
            link = m.group(0)
            if not link.lower().startswith("http"):
                link = "https://" + link
            links.append(link)
        return _dedup(links)

    @staticmethod
    def _derive_signals(text: str, result: ProbeResult) -> list[str]:
        signals: list[str] = []
        low = text.lower()
        hit_keywords = sorted({k for k in RISK_KEYWORDS if k in low})
        if hit_keywords:
            signals.append("Маркеры манипуляции: " + ", ".join(hit_keywords))
        if result.extracted_promises:
            signals.append(
                f"Обещания доходности: {len(result.extracted_promises)} совпадений"
            )
        if result.telegram_links:
            signals.append(
                "Увод в Telegram вне модерации площадки "
                f"({len(result.telegram_links)} ссыл.)"
            )
        if result.extracted_contacts:
            signals.append("Прямые контактные данные в публичном доступе")
        return signals

    # ── скриншот через playwright ──────────────────────────────────
    async def _screenshot(self, url: str, handle: str, ts: str) -> Optional[Path]:
        path = self.evidence_dir / f"{handle}_{ts}.png"
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return None
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                try:
                    page = await browser.new_page(user_agent=USER_AGENT)
                    await page.goto(url, timeout=REQUEST_TIMEOUT * 1000, wait_until="networkidle")
                    await page.screenshot(path=str(path), full_page=True)
                finally:
                    await browser.close()
            return path
        except Exception as exc:  # noqa: BLE001
            self._audit(event="screenshot_failed", handle=handle, error=f"{type(exc).__name__}: {exc}")
            return None

    # ── вспомогательное ────────────────────────────────────────────
    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _audit(self, **entry) -> None:
        """Неизменяемая дозапись в журнал аудита (JSON Lines)."""
        entry.setdefault("logged_at", datetime.now(timezone.utc).isoformat())
        with open(self.audit_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it and it not in seen:
            seen.add(it)
            out.append(it)
    return out


# ───────────────────────────── FastAPI ─────────────────────────────

from fastapi import FastAPI, Header, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402

app = FastAPI(title="АФМ · Probe Agent", version="1.0.0")
_agent = ProbeAgent()

# Демо-хранилище аккаунтов. В проде — выборка из БД/реестра по account_id.
ACCOUNTS: dict[str, dict] = {
    "acc_easy_earn_kz": {
        "platform": "tiktok",
        "handle": "easy_earn_kz",
        "bio_url": "https://example.com/easy-earn",
        "bio_text": "Пассивный доход 30% в месяц 💸 Гарантия вывода. Пиши в Telegram t.me/quick_profit_kz",
    },
    "acc_casino_win_astana": {
        "platform": "instagram",
        "handle": "casino_win_astana",
        "bio_url": None,
        "bio_text": "Бонус на первый депозит! Реферальная программа. t.me/quick_profit_kz +7 (701) 123-45-67",
    },
}


class ProbeRequest(BaseModel):
    account_id: str
    analyst_name: str


def _verify_token(x_analyst_token: Optional[str]) -> None:
    secret = os.getenv("ANALYST_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="ANALYST_SECRET не сконфигурирован на сервере")
    if not x_analyst_token or x_analyst_token != secret:
        raise HTTPException(status_code=401, detail="Неверный или отсутствует X-Analyst-Token")


@app.post("/probe")
async def probe_endpoint(
    body: ProbeRequest,
    x_analyst_token: Optional[str] = Header(default=None, alias="X-Analyst-Token"),
):
    """
    Запуск зондировщика по аккаунту. Требует заголовок X-Analyst-Token
    (сверяется с env ANALYST_SECRET). Возвращает ProbeResult в JSON.
    """
    _verify_token(x_analyst_token)

    account = ACCOUNTS.get(body.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Аккаунт не найден: {body.account_id}")

    result = await _agent.probe(account, approved_by=body.analyst_name)
    return {
        "result": result.to_dict(),
        "evidence_report": result.to_evidence_dict(),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "secret_configured": bool(os.getenv("ANALYST_SECRET"))}
