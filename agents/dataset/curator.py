"""
DatasetCuratorAgent — замыкает цикл самообучения.

Когда аналитик подтверждает кейс (decision=approve), куратор извлекает из
досье текстовые сигналы (транскрипт + OCR), сопоставляет подтверждённый
класс и дописывает строки в data/curated_labeled.csv (Layer 4 датасета) и
метку видео в data/videos_labels.csv (для Component B).

Защита от отравления модели: в обучение попадают ТОЛЬКО подтверждённые
аналитиком кейсы, и только если у кейса есть осмысленный текст.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from ..base import DATA_DIR, Agent, get_case

log = logging.getLogger("sunkar.dataset.curator")

CURATED_CSV = DATA_DIR / "curated_labeled.csv"
VIDEO_LABELS_CSV = DATA_DIR / "videos_labels.csv"


def _label_id(top_class: str) -> int:
    from data.label_schema import NAME_TO_ID

    return NAME_TO_ID.get(top_class, 0)


def _detect_lang(text: str) -> str:
    # грубо: есть кириллица → ru (KZ-специфику не отличаем надёжно), иначе en
    return "ru" if any("а" <= ch.lower() <= "я" or ch in "ёі" for ch in text) else "en"


def _ensure_header(path: Path, header: list[str]) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(header)


def _existing_texts() -> set[str]:
    if not CURATED_CSV.exists():
        return set()
    out = set()
    with open(CURATED_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.add(row.get("text", ""))
    return out


class DatasetCuratorAgent(Agent):
    name = "dataset_curator"

    def curate_case(self, item_id: str, label_override: str | None = None) -> dict:
        """Добавляет тексты подтверждённого кейса в обучающий датасет.
        label_override — если аналитик переопределил класс (имя класса)."""
        case = get_case(item_id)
        if case is None:
            return {"ok": False, "reason": "case_not_found", "added": 0}

        top_class = label_override or case.get("top_class", "clean")
        if top_class == "clean":
            return {"ok": False, "reason": "clean_class_skipped", "added": 0}
        label = _label_id(top_class)

        raw = case.get("raw") or {}
        texts: list[str] = []
        for seg in raw.get("transcript", []):
            t = (seg.get("text") or "").strip()
            if len(t) > 3:
                texts.append(t)
        for seg in raw.get("ocr", []):
            t = (seg.get("text") or "").strip()
            if len(t) > 3:
                texts.append(t)
        # подпись видео тоже сигнал
        cap = (case.get("caption") or "").strip()
        if len(cap) > 3:
            texts.append(cap)

        if not texts:
            return {"ok": False, "reason": "no_text_signal", "added": 0}

        _ensure_header(CURATED_CSV, ["text", "label", "lang", "source", "case_id"])
        seen = _existing_texts()
        added = 0
        with open(CURATED_CSV, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            for t in dict.fromkeys(texts):  # дедуп внутри кейса, порядок сохранён
                if t in seen:
                    continue
                w.writerow([t, label, _detect_lang(t), "confirmed_case", item_id])
                seen.add(t)
                added += 1

        # метка видео для Component B (1 = fraud)
        _ensure_header(VIDEO_LABELS_CSV, ["video_id", "risk_label"])
        with open(VIDEO_LABELS_CSV, "a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow([item_id, 1])

        self.log_action("curated", item_id=item_id, label=label, added=added)
        return {"ok": True, "item_id": item_id, "label": label, "top_class": top_class, "added": added}

    def stats(self) -> dict:
        n_text = max(0, sum(1 for _ in open(CURATED_CSV, encoding="utf-8")) - 1) if CURATED_CSV.exists() else 0
        n_video = max(0, sum(1 for _ in open(VIDEO_LABELS_CSV, encoding="utf-8")) - 1) if VIDEO_LABELS_CSV.exists() else 0
        return {"curated_text_rows": n_text, "labeled_videos": n_video}
