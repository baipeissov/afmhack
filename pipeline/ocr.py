"""
Видео -> 1 кадр/сек (ffmpeg) -> текст на экране (PaddleOCR, поддержка
кириллицы) -> [{frame_time, text}].

Текст на экране — отдельный канал сигнала от речи: скам-видео часто кладёт
ключевую информацию (номер телефона, "+847 000 ₸ за 3 дня", ссылку) именно
оверлеем на экран, а не голосом.
"""

import subprocess
import tempfile
from pathlib import Path

try:
    from .ffmpeg_util import get_ffmpeg_path
except ImportError:
    from ffmpeg_util import get_ffmpeg_path

_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR

        # lang="ru" покрывает кириллицу; PaddleOCR детектит текст независимо
        # от языка, lang влияет на модель распознавания символов.
        # PaddleOCR 3.x: use_textline_orientation заменил use_angle_cls,
        # show_log больше не поддерживается.
        _ocr = PaddleOCR(use_textline_orientation=True, lang="ru")
    return _ocr


def _extract_frames(video_path: str, out_dir: str, fps: int = 1) -> list[Path]:
    pattern = str(Path(out_dir) / "frame_%05d.jpg")
    subprocess.run(
        [get_ffmpeg_path(), "-y", "-i", video_path, "-vf", f"fps={fps}", pattern],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return sorted(Path(out_dir).glob("frame_*.jpg"))


def extract_overlay_text(video_path: str, fps: int = 1) -> list[dict]:
    ocr = _get_ocr()
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        frames = _extract_frames(video_path, tmp, fps=fps)
        for i, frame_path in enumerate(frames):
            frame_time = round(i / fps, 2)
            ocr_out = ocr.predict(str(frame_path))
            lines = []
            for page in ocr_out or []:
                texts = page.get("rec_texts", [])
                scores = page.get("rec_scores", [])
                for text, conf in zip(texts, scores):
                    if conf > 0.5 and text.strip():
                        lines.append(text.strip())
            if lines:
                results.append({"frame_time": frame_time, "text": " ".join(lines)})
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python pipeline/ocr.py <video_path>")
        sys.exit(1)
    for r in extract_overlay_text(sys.argv[1]):
        print(f"[{r['frame_time']:.1f}s] {r['text']}")
