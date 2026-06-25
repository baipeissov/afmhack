"""
Сборка итогового досье по одному видео: прогоняет все модальности,
применяет Component A к транскрипту и OCR, считает risk score через
Component B (fusion), формирует человекочитаемые RU-объяснения с
таймкодами — то, что аналитик может скопировать прямо в отчёт.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.label_schema import LABELS_RU  # noqa: E402
from models import fusion_predict, predict_text  # noqa: E402
from pipeline import audio, entity_extractor, llm_explainer, metadata, ocr, visual  # noqa: E402

try:
    from pipeline.kaspi_normalizer import find_kaspi_numbers
except ImportError:  # модуль ещё не готов/не подключён — сеть просто без телефонов
    find_kaspi_numbers = None

FRAUD_CLASS_NAMES = [LABELS_RU[i] for i in fusion_predict.FRAUD_CLASS_IDS]
RISK_LEVELS = [(0.7, "HIGH"), (0.4, "MEDIUM"), (0.0, "LOW")]


def _risk_level(score: float) -> str:
    for threshold, label in RISK_LEVELS:
        if score >= threshold:
            return label
    return "LOW"


def _aggregate_text_class_probs(rows: list[dict], text_key: str) -> tuple[dict, list[dict]]:
    """Прогоняет Component A по каждому сегменту (транскрипт/OCR), берёт
    максимум по каждому классу как агрегат на уровне видео + список evidence
    по сегментам, где модель уверена в каком-то fraud-классе."""
    if not rows:
        return {}, []

    texts = [r[text_key] for r in rows]
    preds = predict_text.predict_batch(texts)

    agg = {}
    for p in preds:
        for cls, prob in p["class_probs"].items():
            agg[cls] = max(agg.get(cls, 0.0), prob)

    evidence = []
    for row, pred in zip(rows, preds):
        top = pred["top_class"]
        if top == "clean":
            continue
        prob = pred["class_probs"][top]
        if prob < 0.5:
            continue
        evidence.append({"row": row, "class": top, "prob": prob})
    return agg, evidence


def build_dossier(video_path: str, account_metadata: dict | None = None, caption: str | None = None) -> dict:
    transcript = audio.transcribe(video_path)
    ocr_rows = ocr.extract_overlay_text(video_path)
    visual_rows = visual.score_frames(video_path)
    meta_features = metadata.normalize(account_metadata)

    transcript_probs, transcript_evidence = _aggregate_text_class_probs(transcript, "text")
    ocr_probs, ocr_evidence = _aggregate_text_class_probs(ocr_rows, "text")

    all_text = [r["text"] for r in transcript] + [r["text"] for r in ocr_rows] + ([caption] if caption else [])
    entities = entity_extractor.extract_entities(all_text)
    if find_kaspi_numbers:
        phones: set[str] = set()
        for text in all_text:
            phones.update(find_kaspi_numbers(text))
        entities["phones"] = sorted(phones)

    visual_scores_max = {}
    visual_evidence = []
    for row in visual_rows:
        for marker, score in row["scores"].items():
            if score > visual_scores_max.get(marker, 0.0):
                visual_scores_max[marker] = score
        top_marker, top_score = max(row["scores"].items(), key=lambda kv: kv[1])
        if top_score > 0.26:  # эмпирический порог для ViT-B/32 zero-shot
            visual_evidence.append({"frame_time": row["frame_time"], "marker": top_marker, "score": top_score})

    features = fusion_predict.build_feature_vector(transcript_probs, ocr_probs, visual_scores_max, meta_features)
    risk = fusion_predict.predict_risk(features)

    top_text_class = max(transcript_probs.items(), key=lambda kv: kv[1])[0] if transcript_probs else "clean"

    explanations = []
    for e in transcript_evidence:
        t = e["row"]["start"]
        explanations.append(
            f"🔴 [{int(t // 60):02d}:{int(t % 60):02d}] Аудио: \"{e['row']['text']}\" "
            f"→ {LABELS_RU[_class_id(e['class'])]} (p={e['prob']:.2f})"
        )
    for e in visual_evidence:
        t = e["frame_time"]
        explanations.append(
            f"🔴 [кадр {int(t // 60):02d}:{int(t % 60):02d}] Визуал: {e['marker']} (CLIP {e['score']:.2f})"
        )
    for e in ocr_evidence:
        t = e["row"]["frame_time"]
        explanations.append(
            f"🟡 [overlay {int(t // 60):02d}:{int(t % 60):02d}] OCR: \"{e['row']['text']}\" "
            f"→ {LABELS_RU[_class_id(e['class'])]} (p={e['prob']:.2f})"
        )
    if meta_features.get("account_age_risk", 0) > 0.5 or meta_features.get("follower_growth_risk", 0) > 0.5:
        explanations.append(
            f"🟡 Метаданные: возраст аккаунта/рост подписчиков подозрительны "
            f"(age_risk={meta_features.get('account_age_risk', 0):.2f}, "
            f"growth_risk={meta_features.get('follower_growth_risk', 0):.2f})"
        )

    # LLM-объяснение по таймкодам: берём топ-3 evidence-сегмента по уверенности
    # (аудио и OCR вместе) и просим маленькую локальную LLM объяснить фразу
    # человеческим языком — поверх уже готовых шаблонных explanations выше.
    # Если Ollama не запущен, llm_explainer тихо вернёт [] — не блокирует досье.
    llm_evidence = [{**e, "class_ru": LABELS_RU[_class_id(e["class"])]} for e in transcript_evidence] + [
        {**e, "class_ru": LABELS_RU[_class_id(e["class"])]} for e in ocr_evidence
    ]
    llm_evidence.sort(key=lambda e: -e["prob"])
    llm_explanations = llm_explainer.explain_evidence(llm_evidence, max_items=3)

    recommendation = (
        "Направить аналитику на приоритетную проверку (priority 1)"
        if risk["risk_score"] >= 0.7
        else "Направить на стандартную проверку"
        if risk["risk_score"] >= 0.4
        else "Низкий риск — без приоритизации"
    )

    return {
        "video_path": video_path,
        "risk_score": risk["risk_score"],
        "risk_level": _risk_level(risk["risk_score"]),
        "top_class": top_text_class,
        "top_class_ru": LABELS_RU.get(_class_id(top_text_class), top_text_class),
        "contributions": risk["contributions"],
        "explanations": explanations,
        "llm_explanations": llm_explanations,
        "recommendation": recommendation,
        "entities": entities,
        "raw": {
            "transcript": transcript,
            "ocr": ocr_rows,
            "visual": visual_rows,
            "metadata_features": meta_features,
        },
    }


def _class_id(name: str) -> int:
    from data.label_schema import NAME_TO_ID

    return NAME_TO_ID[name]


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("usage: python api/dossier.py <video_path>")
        sys.exit(1)
    dossier = build_dossier(sys.argv[1])
    print(json.dumps(dossier, ensure_ascii=False, indent=2))
