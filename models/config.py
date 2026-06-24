"""Единое место для путей и имён моделей — чтобы свапнуть e5-base на
e5-small (если CPU на сцене окажется медленным) одной строкой."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
# e5 рекомендует префиксы "query: " / "passage: " для лучшего качества
# эмбеддингов. Для классификации (не retrieval) используем единый префикс.
E5_PREFIX = "query: "


def get_device() -> str:
    """CPU-сборка torch стоит в requirements.txt намеренно (переносимость на
    машины жюри без GPU), но если на ЭТОЙ машине доступен Apple MPS — грех не
    использовать его для инференса/обучения, это сильно быстрее CPU."""
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

WEIGHTS_DIR = ROOT / "models" / "weights"
TEXT_CLASSIFIER_PATH = WEIGHTS_DIR / "text_classifier.joblib"
METRICS_DIR = ROOT / "models" / "metrics"

TRAIN_CSV = ROOT / "data" / "train.csv"
