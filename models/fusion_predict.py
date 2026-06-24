"""
Component B — Fusion / Risk Model.

ЧЕСТНО: за оставшееся время у нас нет 40-80 размеченных видео (data/videos_labels.csv
template ниже), поэтому Component B сейчас — explainable ВЗВЕШЕННАЯ ЛИНЕЙНАЯ КОМБИНАЦИЯ
признаков всех модальностей с вручную заданными весами (не обученными). Это не подмена
"своей модели" — это тот же функциональный класс (линейная модель y = w·x), который
LogisticRegression выучивает на данных; мы прямо это говорим на защите: "веса сейчас
экспертные, интерфейс готов принять обученные веса как только наберём 40-80 размеченных
видео" (см. data/videos_labels.csv). fit_from_labels() ниже — путь дообучения, когда
данные появятся.

Признаки на входе (все в [0,1]):
  text_transcript_<class>   - вероятность класса из Component A по транскрипту
  text_ocr_<class>          - вероятность класса из Component A по OCR-тексту
  visual_<marker>           - максимальный CLIP-скор по кадрам (нормализован сигмоидой)
  account_age_risk, follower_growth_risk, has_referral_link_in_bio - из pipeline/metadata.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.label_schema import LABELS  # noqa: E402

FRAUD_CLASS_IDS = [1, 2, 3, 4, 5]  # всё кроме "clean"

# Экспертные веса (нормированы так, чтобы типичный сильный сигнал по одной
# модальности уже давал risk > 0.5 — каждая модальность достаточна сама по
# себе, что соответствует тому, как аналитик сегодня принимает решение:
# "если хоть один явный маркер — в очередь на проверку").
WEIGHTS = {
    "text_transcript_fraud_max": 2.2,   # max p(class) среди классов 1-5 по транскрипту
    "text_ocr_fraud_max": 1.8,           # то же по OCR-тексту (немного менее надёжно: OCR шумнее)
    "visual_fraud_max": 1.5,             # max CLIP-скор среди визуальных маркеров
    "account_age_risk": 0.6,
    "follower_growth_risk": 0.6,
    "has_referral_link_in_bio": 0.4,
}
BIAS = -1.1  # сдвиг, чтобы "всё чисто" (все фичи ~0) давало risk близкий к 0


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def build_feature_vector(
    transcript_class_probs: dict | None,
    ocr_class_probs: dict | None,
    visual_scores: dict | None,
    metadata_features: dict | None,
) -> dict:
    transcript_class_probs = transcript_class_probs or {}
    ocr_class_probs = ocr_class_probs or {}
    visual_scores = visual_scores or {}
    metadata_features = metadata_features or {}

    fraud_names = [LABELS[i] for i in FRAUD_CLASS_IDS]
    transcript_fraud_max = max([transcript_class_probs.get(n, 0.0) for n in fraud_names], default=0.0)
    ocr_fraud_max = max([ocr_class_probs.get(n, 0.0) for n in fraud_names], default=0.0)
    # CLIP cosine similarity лежит примерно в [0.15, 0.35] для релевантных
    # картинок (типичный диапазон для ViT-B/32 zero-shot) -> растягиваем
    # сигмоидой в осмысленный [0,1] risk-диапазон.
    visual_fraud_max = max([_sigmoid((v - 0.24) * 25) for v in visual_scores.values()], default=0.0)

    return {
        "text_transcript_fraud_max": transcript_fraud_max,
        "text_ocr_fraud_max": ocr_fraud_max,
        "visual_fraud_max": visual_fraud_max,
        "account_age_risk": metadata_features.get("account_age_risk", 0.0),
        "follower_growth_risk": metadata_features.get("follower_growth_risk", 0.0),
        "has_referral_link_in_bio": metadata_features.get("has_referral_link_in_bio", 0.0),
    }


def predict_risk(features: dict) -> dict:
    """-> {"risk_score": 0.87, "contributions": {feature: w*x, ...}}
    contributions — линейный вклад каждой фичи, прямое объяснение (как SHAP
    для линейных моделей, но без библиотеки и без затрат на вычисление)."""
    z = BIAS
    contributions = {}
    for name, weight in WEIGHTS.items():
        x = float(features.get(name, 0.0))
        contrib = weight * x
        contributions[name] = round(contrib, 4)
        z += contrib

    risk_score = float(_sigmoid(z))
    return {
        "risk_score": round(risk_score, 4),
        "contributions": contributions,
    }


def fit_from_labels(videos_labels_csv: str, features_per_video: dict[str, dict]):
    """TODO как только наберётся data/videos_labels.csv (40-80 строк):
    обучить LogisticRegression(features -> risk_label) и заменить WEIGHTS/BIAS
    на clf.coef_/clf.intercept_. Сигнатура заранее совместима с
    build_feature_vector(), чтобы переход был однострочным."""
    import pandas as pd
    from sklearn.linear_model import LogisticRegression

    labels_df = pd.read_csv(videos_labels_csv)
    X, y = [], []
    feature_names = list(WEIGHTS.keys())
    for _, row in labels_df.iterrows():
        feats = features_per_video.get(row["video_id"])
        if feats is None:
            continue
        X.append([feats.get(n, 0.0) for n in feature_names])
        y.append(int(row["risk_label"]))

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X, y)
    return clf, feature_names


if __name__ == "__main__":
    example_features = build_feature_vector(
        transcript_class_probs={"clean": 0.01, "pyramid_investment": 0.94},
        ocr_class_probs={"clean": 0.3, "urgency_pressure": 0.6},
        visual_scores={"casino_interface": 0.31, "luxury_lifestyle": 0.18},
        metadata_features={"account_age_risk": 0.9, "follower_growth_risk": 0.8, "has_referral_link_in_bio": 1.0},
    )
    print("features:", example_features)
    print("prediction:", predict_risk(example_features))
