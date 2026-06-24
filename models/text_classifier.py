"""
Component A — Fraud Text Classifier.

multilingual-e5-base (заморожен, не файнтюним веса трансформера — на CPU
за 24ч это нереалистично) + калиброванная LogisticRegression-голова сверху
эмбеддингов. Это и есть "своя модель": веса головы обучены нами на нашем
датасете и нашей 6-классовой схеме, эмбеддер используется как фиксированный
feature extractor (стандартная и абсолютно легитимная практика, как
ImageNet-backbone в CV) — собственной частью является классификационная
голова + сама разметка/схема классов.

Обучает CalibratedClassifierCV(LogisticRegression) -> calibrated probs,
печатает classification_report + confusion matrix, сохраняет:
  models/weights/text_classifier.joblib   (sklearn pipeline: голова)
  models/metrics/classification_report.json
  models/metrics/confusion_matrix.png
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.label_schema import LABELS  # noqa: E402
from models.config import (  # noqa: E402
    E5_PREFIX,
    EMBEDDING_MODEL_NAME,
    METRICS_DIR,
    TEXT_CLASSIFIER_PATH,
    TRAIN_CSV,
    WEIGHTS_DIR,
    get_device,
)


def embed_texts(texts: list[str], model) -> np.ndarray:
    prefixed = [E5_PREFIX + t for t in texts]
    return model.encode(prefixed, batch_size=32, show_progress_bar=True, normalize_embeddings=True)


def main():
    print(f"Loading {TRAIN_CSV} ...")
    df = pd.read_csv(TRAIN_CSV).dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)
    print(df["label"].value_counts().sort_index())

    print(f"Loading embedding model {EMBEDDING_MODEL_NAME} (this can take a while on first run)...")
    from sentence_transformers import SentenceTransformer

    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    X_train_text, X_test_text, y_train, y_test = train_test_split(
        df["text"].tolist(),
        df["label"].tolist(),
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    print(f"Embedding {len(X_train_text)} train + {len(X_test_text)} test texts...")
    X_train = embed_texts(X_train_text, embedder)
    X_test = embed_texts(X_test_text, embedder)

    print("Training CalibratedClassifierCV(LogisticRegression)...")
    base = LogisticRegression(max_iter=2000, class_weight="balanced")
    clf = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    target_names = [LABELS[i] for i in sorted(LABELS)]
    report = classification_report(
        y_test, y_pred, target_names=target_names, output_dict=True, zero_division=0
    )
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=sorted(LABELS))

    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump({"classifier": clf, "embedding_model_name": EMBEDDING_MODEL_NAME, "e5_prefix": E5_PREFIX}, TEXT_CLASSIFIER_PATH)
    print(f"Saved classifier head -> {TEXT_CLASSIFIER_PATH}")

    with open(METRICS_DIR / "classification_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    np.save(METRICS_DIR / "confusion_matrix.npy", cm)

    _plot_confusion_matrix(cm, target_names, METRICS_DIR / "confusion_matrix.png")
    print(f"Saved metrics -> {METRICS_DIR}")


def _plot_confusion_matrix(cm, labels, out_path):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Component A — confusion matrix")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
