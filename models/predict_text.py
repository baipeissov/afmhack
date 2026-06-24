"""
Инференс Component A. Используется и для транскрипта (audio.py), и для
OCR-текста (ocr.py) — один и тот же классификатор применяется к обоим
текстовым каналам, fusion-модель (Step 5) объединяет результаты.
"""

import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.label_schema import LABELS  # noqa: E402
from models.config import TEXT_CLASSIFIER_PATH, get_device  # noqa: E402

_bundle = None
_embedder = None


def _load():
    global _bundle, _embedder
    if _bundle is None:
        _bundle = joblib.load(TEXT_CLASSIFIER_PATH)
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer(_bundle["embedding_model_name"], device=get_device())
    return _bundle, _embedder


def predict(text: str) -> dict:
    """-> {"top_class": "pyramid_investment", "top_class_id": 2,
           "class_probs": {"clean": 0.01, ..., "pyramid_investment": 0.94, ...}}"""
    bundle, embedder = _load()
    clf = bundle["classifier"]
    prefix = bundle["e5_prefix"]

    emb = embedder.encode([prefix + text], normalize_embeddings=True)
    probs = clf.predict_proba(emb)[0]

    class_probs = {LABELS[i]: round(float(p), 4) for i, p in enumerate(probs)}
    top_id = int(probs.argmax())
    return {
        "top_class": LABELS[top_id],
        "top_class_id": top_id,
        "class_probs": class_probs,
    }


def predict_batch(texts: list[str]) -> list[dict]:
    bundle, embedder = _load()
    clf = bundle["classifier"]
    prefix = bundle["e5_prefix"]

    embs = embedder.encode([prefix + t for t in texts], normalize_embeddings=True)
    probs = clf.predict_proba(embs)

    results = []
    for row in probs:
        class_probs = {LABELS[i]: round(float(p), 4) for i, p in enumerate(row)}
        top_id = int(row.argmax())
        results.append({"top_class": LABELS[top_id], "top_class_id": top_id, "class_probs": class_probs})
    return results


if __name__ == "__main__":
    examples = [
        "Гарантирую доход x5 за месяц без риска, инвестируй сейчас.",
        "Сегодня я ходила в парк с друзьями.",
        "Напиши + в комментариях, пришлю детали в директ.",
    ]
    for ex in examples:
        print(ex, "->", predict(ex))
