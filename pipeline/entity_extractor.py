"""
Извлечение публичных "общих сигналов" из текста видео (транскрипт + OCR +
caption) для построения сети связанных аккаунтов (см. /network на фронте).

Идея: мошеннические схемы используют один и тот же Telegram-канал /
реферальную ссылку / хэштег на нескольких внешне независимых аккаунтах —
это и есть связь, которую видит аналитик на графе. Регулярки работают на
тексте, который мы уже легально извлекли (caption видео, ASR, OCR) — без
дополнительного скрейпинга профиля или сбора подписчиков.

Номера телефонов сюда не входят — за это отвечает pipeline/kaspi_normalizer.py.
"""

import re
from urllib.parse import urlsplit, urlunsplit

_TELEGRAM_RE = re.compile(r"(?:https?://)?t\.me/([A-Za-z0-9_]{4,32})", re.IGNORECASE)
_HASHTAG_RE = re.compile(r"#([\wа-яёА-ЯЁ]{2,40})", re.UNICODE)
_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_REFERRAL_PARAM_RE = re.compile(r"(?:^|[?&])(ref|promo|aff|invite|partner)=", re.IGNORECASE)


def _normalize_referral_link(url: str) -> str:
    """Схема + хост + путь, без query — несколько аккаунтов обычно ведут на
    одну и ту же landing page с разным персональным ref-кодом в query."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def extract_entities(texts: list[str]) -> dict[str, list[str]]:
    """texts: тексты сегментов (транскрипт/OCR/caption), уже извлечённые
    легальным путём. Возвращает дедуплицированные списки сущностей по типу."""
    telegram: set[str] = set()
    hashtags: set[str] = set()
    referral_links: set[str] = set()

    for text in texts:
        if not text:
            continue
        for m in _TELEGRAM_RE.finditer(text):
            telegram.add(m.group(1).lower())
        for m in _HASHTAG_RE.finditer(text):
            hashtags.add(m.group(1).lower())
        for url in _URL_RE.findall(text):
            if _REFERRAL_PARAM_RE.search(url):
                referral_links.add(_normalize_referral_link(url))

    return {
        "telegram": sorted(telegram),
        "referral_links": sorted(referral_links),
        "hashtags": sorted(hashtags),
    }


if __name__ == "__main__":
    sample = [
        "Подписывайся на наш канал t.me/quick_profit_kz, гарантированный доход!",
        "Переходи по ссылке https://invest-pro.kz/landing?ref=ab12 прямо сейчас",
        "#инвестиции #пирамида #казахстаниинвест",
    ]
    print(extract_entities(sample))
