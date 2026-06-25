"""
Анализ "прямого эфира" по чанкам, без ожидания конца видео.

Для демо на сцене сознательно НЕ делаем живой захват HLS с реальной
платформы (TikTok/Instagram LIVE) — захват зависит от сети на площадке и от
того, идёт ли в этот момент реальный эфир, что слишком хрупко для 5-минутного
слота. Вместо этого режем уже скачанный видеофайл на чанки по
chunk_seconds и прогоняем через build_dossier() каждый чанк отдельно — это
честно демонстрирует механику "анализируем каждые 30 секунд, не дожидаясь
конца эфира", потому что build_dossier() ничего не знает о длине видео и
одинаково работает и на полном видео, и на 30-секундном куске.

Реальный живой захват (capture_live_chunks) оставлен как рабочий путь для
прода/будущего, но помечен как НЕ для сцены — слишком много внешних
переменных (антибот платформы, доступность HLS-манифеста) для live-демо.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator

try:
    from .ffmpeg_util import get_ffmpeg_path
except ImportError:
    from ffmpeg_util import get_ffmpeg_path

logger = logging.getLogger("live_stream")

DEFAULT_CHUNK_SECONDS = 30


def chunk_video(video_path: str, out_dir: str, chunk_seconds: int = DEFAULT_CHUNK_SECONDS) -> list[Path]:
    """Режет видеофайл на чанки по chunk_seconds без перекодирования
    (-c copy — быстро, секунды, а не минуты) и сбрасывает таймстемпы внутри
    каждого чанка на 0, чтобы audio.transcribe/ocr давали таймкоды
    относительно начала чанка."""
    pattern = str(Path(out_dir) / "chunk_%03d.mp4")
    subprocess.run(
        [
            get_ffmpeg_path(), "-y", "-i", video_path,
            "-c", "copy", "-map", "0",
            "-f", "segment", "-segment_time", str(chunk_seconds), "-reset_timestamps", "1",
            pattern,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return sorted(Path(out_dir).glob("chunk_*.mp4"))


def analyze_chunks(
    video_path: str,
    chunk_seconds: int = DEFAULT_CHUNK_SECONDS,
    account_metadata: dict | None = None,
) -> Iterator[dict]:
    """Генератор: режет видео на чанки и yield-ит частичное досье по каждому
    чанку по мере готовности — вызывающий код (например, эндпоинт /analyze/live
    с BackgroundTasks) может писать каждый результат в очередь сразу, не
    дожидаясь конца всего видео."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from api.dossier import build_dossier  # noqa: E402  (ленивый импорт — избегаем цикла pipeline<->api)

    with tempfile.TemporaryDirectory() as tmp:
        chunks = chunk_video(video_path, tmp, chunk_seconds=chunk_seconds)
        for i, chunk_path in enumerate(chunks):
            stream_offset_seconds = i * chunk_seconds
            try:
                dossier = build_dossier(str(chunk_path), account_metadata)
            except Exception as e:  # noqa: BLE001 — один плохой чанк не должен убить весь live-анализ
                logger.warning("chunk %d failed, skipping: %s", i, e)
                continue
            yield {
                "chunk_index": i,
                "stream_offset_seconds": stream_offset_seconds,
                "dossier": dossier,
            }


def capture_live_chunks(stream_url: str, out_dir: str, chunk_seconds: int = DEFAULT_CHUNK_SECONDS, max_chunks: int = 20) -> Iterator[str]:
    """Реальный захват прямого эфира по чанкам через yt-dlp + ffmpeg.

    НЕ используется в демо на сцене (см. docstring модуля) — оставлен как
    рабочий прототип для прода. Каждый цикл получает текущий HLS-манифест
    (yt-dlp -g) и пишет ровно chunk_seconds эфира; если платформа блокирует
    доступ или эфир закончился — просто логируем и останавливаемся, не
    пытаемся обойти защиту."""
    import yt_dlp

    for i in range(max_chunks):
        opts = {"quiet": True, "no_warnings": True, "skip_download": True, "format": "best"}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(stream_url, download=False)
            hls_url = info.get("url")
        except Exception as e:  # noqa: BLE001
            logger.warning("live stream unavailable, stopping capture: %s", e)
            return
        if not hls_url:
            logger.warning("no stream url resolved, stopping capture")
            return

        chunk_path = str(Path(out_dir) / f"live_chunk_{i:03d}.mp4")
        try:
            subprocess.run(
                [get_ffmpeg_path(), "-y", "-i", hls_url, "-t", str(chunk_seconds), "-c", "copy", chunk_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=chunk_seconds + 15,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning("chunk %d capture failed, stopping: %s", i, e)
            return
        yield chunk_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python pipeline/live_stream.py <video_path> [chunk_seconds]")
        sys.exit(1)
    chunk_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CHUNK_SECONDS
    for result in analyze_chunks(sys.argv[1], chunk_seconds=chunk_seconds):
        d = result["dossier"]
        print(
            f"[t+{result['stream_offset_seconds']}s] чанк {result['chunk_index']}: "
            f"risk={d['risk_score']:.2f} ({d['risk_level']}) — {d['top_class_ru']}"
        )
        for line in d["explanations"]:
            print(f"   {line}")
