"""
Скачивание видео по URL + автоматическое извлечение метадаты через yt-dlp —
тот же механизм, что используют connectors/tiktok_connector.py и
instagram_connector.py для автообнаружения, только по явно заданной ссылке
(аналитик вставляет URL — caption и @handle вытягиваются сами, без ручного
ввода).
"""

import logging
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger("url_fetch")


def _detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "tiktok" in host:
        return "TikTok"
    if "instagram" in host:
        return "Instagram"
    return "Unknown"


def fetch_video(url: str, out_dir: Path) -> dict:
    """Скачивает видео по URL, возвращает {local_path, caption,
    account_handle, platform}. Поднимает исключение, если yt-dlp не смог
    обработать ссылку (приватный/удалённый пост, неподдерживаемая
    платформа) — вызывающий код решает, как сообщить об этом аналитику."""
    import yt_dlp

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(out_dir / "url_%(id)s.%(ext)s")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "mp4/best",
        "outtmpl": out_template,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        local_path = ydl.prepare_filename(info)

    return {
        "local_path": local_path,
        "caption": info.get("description") or "",
        "account_handle": info.get("uploader") or info.get("channel") or None,
        "platform": _detect_platform(url),
    }
