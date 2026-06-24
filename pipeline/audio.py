"""
Видео -> аудио (ffmpeg) -> транскрипт с таймкодами (faster-whisper, локально).

Используем faster-whisper (CTranslate2-инференс) вместо openai-whisper —
заметно быстрее на CPU, что критично для демо без GPU на сцене.
"""

import subprocess
import tempfile
from pathlib import Path

try:
    from .ffmpeg_util import get_ffmpeg_path
except ImportError:  # запущен напрямую как python pipeline/audio.py
    from ffmpeg_util import get_ffmpeg_path

MODEL_SIZE = "small"  # swap-friendly: "tiny"/"base"/"small"/"medium"
_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def extract_audio(video_path: str, out_wav: str) -> str:
    """ffmpeg: видео -> mono 16kHz WAV (формат, который ждёт Whisper)."""
    subprocess.run(
        [
            get_ffmpeg_path(), "-y", "-i", video_path,
            "-ac", "1", "-ar", "16000", "-vn",
            out_wav,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out_wav


def transcribe(video_path: str) -> list[dict]:
    """Возвращает [{start, end, text}] с таймкодами в секундах."""
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = extract_audio(video_path, str(Path(tmp) / "audio.wav"))
        model = _get_model()
        segments, _info = model.transcribe(wav_path, language=None, vad_filter=True)
        return [
            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segments
        ]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python pipeline/audio.py <video_path>")
        sys.exit(1)
    for seg in transcribe(sys.argv[1]):
        print(f"[{seg['start']:.1f}-{seg['end']:.1f}] {seg['text']}")
