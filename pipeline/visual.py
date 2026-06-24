"""
Видео -> кадры (ffmpeg) -> CLIP zero-shot против списка визуальных
промптов-маркеров (казино-интерфейс, роскошь, трейдинг-терминал, пирамида,
скрин "дохода") -> per-frame оценки сходства.

Zero-shot означает: НЕ нужно размечать и обучать отдельный визуальный
классификатор для каждого нового маркера — достаточно добавить
текстовый промпт в PROMPTS. Это тоже часть "своей модели": сама схема
маркеров и пороги — наши, CLIP используется как замороженный backbone
(как и e5 в Component A).
"""

import subprocess
import tempfile
from pathlib import Path

try:
    from .ffmpeg_util import get_ffmpeg_path
except ImportError:
    from ffmpeg_util import get_ffmpeg_path

MODEL_NAME = "ViT-B-32"
PRETRAINED = "openai"

PROMPTS = {
    "casino_interface": "screenshot of an online casino or slot machine game interface",
    "luxury_lifestyle": "photo of luxury cars, stacks of cash, or expensive watches",
    "trading_terminal": "screenshot of a trading or stock market terminal with charts",
    "pyramid_diagram": "a pyramid or multi-level marketing network diagram",
    "fake_income_screenshot": "a screenshot of a bank app or wallet showing a large money transfer",
}

_model = None
_preprocess = None
_tokenizer = None
_text_features = None


def _get_model():
    global _model, _preprocess, _tokenizer, _text_features
    if _model is None:
        import open_clip
        import torch

        _model, _, _preprocess = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=PRETRAINED)
        _tokenizer = open_clip.get_tokenizer(MODEL_NAME)
        _model.eval()

        labels = list(PROMPTS.keys())
        texts = _tokenizer([PROMPTS[k] for k in labels])
        with torch.no_grad():
            feats = _model.encode_text(texts)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        _text_features = (labels, feats)
    return _model, _preprocess, _text_features


def _extract_frames(video_path: str, out_dir: str, every_n_seconds: int = 2) -> list[Path]:
    pattern = str(Path(out_dir) / "frame_%05d.jpg")
    subprocess.run(
        [get_ffmpeg_path(), "-y", "-i", video_path, "-vf", f"fps=1/{every_n_seconds}", pattern],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return sorted(Path(out_dir).glob("frame_*.jpg"))


def score_frames(video_path: str, every_n_seconds: int = 2) -> list[dict]:
    import torch
    from PIL import Image

    model, preprocess, (labels, text_features) = _get_model()
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        frames = _extract_frames(video_path, tmp, every_n_seconds=every_n_seconds)
        for i, frame_path in enumerate(frames):
            frame_time = round(i * every_n_seconds, 2)
            image = preprocess(Image.open(frame_path)).unsqueeze(0)
            with torch.no_grad():
                image_features = model.encode_image(image)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                sims = (image_features @ text_features.T).squeeze(0)
            scores = {label: round(float(sim), 4) for label, sim in zip(labels, sims)}
            results.append({"frame_time": frame_time, "scores": scores})
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python pipeline/visual.py <video_path>")
        sys.exit(1)
    for r in score_frames(sys.argv[1]):
        top = max(r["scores"].items(), key=lambda kv: kv[1])
        print(f"[{r['frame_time']:.1f}s] top={top[0]} ({top[1]:.2f})  all={r['scores']}")
