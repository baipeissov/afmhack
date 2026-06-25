"""
Скачивание публичного видео по URL через yt-dlp (как в существующих
коннекторах). Используется browser- и API-коннекторами после того, как
они обнаружили URL мошеннического видео.

Этический периметр: качаем только публичные URL, без логина и обхода
капчи; ограничиваем длительность.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("sunkar.discovery.download")

ROOT = Path(__file__).resolve().parents[2]
INCOMING_DIR = ROOT / "data" / "incoming"
MAX_VIDEO_DURATION_SECONDS = 600


def download_video(url: str, item_id: str, incoming_dir: Path = INCOMING_DIR) -> dict | None:
    """Скачивает видео по url. Возвращает {local_path, caption, account_handle}
    или None при ошибке/блоке. item_id определяет имя файла."""
    import yt_dlp

    incoming_dir = Path(incoming_dir)
    incoming_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(incoming_dir / f"{item_id}.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "mp4/best",
        "outtmpl": out_template,
        "match_filter": yt_dlp.utils.match_filter_func(
            f"duration < {MAX_VIDEO_DURATION_SECONDS}"
        ),
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            local_path = ydl.prepare_filename(info)
    except Exception as e:  # noqa: BLE001
        logger.warning("download failed for %s: %s", url, e)
        return None

    info = info if isinstance(info, dict) else {}
    return {
        "local_path": local_path,
        "caption": info.get("description", "") or "",
        "account_handle": info.get("uploader") or info.get("uploader_id"),
    }
