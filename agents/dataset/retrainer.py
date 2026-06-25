"""
RetrainerAgent — переобучение Component A на пополненном датасете.

Шаги (через существующие скрипты, без дублирования логики обучения):
  1. scripts/build_dataset.py  → пересобирает data/train.csv (теперь с Layer 4:
     confirmed_case из curated_labeled.csv).
  2. models/text_classifier.py → обучает классификатор, кладёт веса в
     models/weights/text_classifier.joblib и метрики в models/metrics/.
  3. Архивируем веса с таймстемпом (версионирование) и возвращаем метрики.

Тяжёлый шаг (нужен torch + datasets), поэтому запускается по кнопке/порогу,
а не на каждый approve. Безопасно вызывать на сервере/машине с ML-стеком.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..base import ROOT, Agent

log = logging.getLogger("sunkar.dataset.retrainer")

WEIGHTS = ROOT / "models" / "weights" / "text_classifier.joblib"
METRICS = ROOT / "models" / "metrics" / "classification_report.json"
ARCHIVE_DIR = ROOT / "models" / "weights" / "archive"


class RetrainerAgent(Agent):
    name = "retrainer"

    def _run(self, *args: str) -> tuple[bool, str]:
        cmd = [sys.executable, *args]
        log.info("run: %s", " ".join(cmd))
        try:
            proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=3600)
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {e}"
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return proc.returncode == 0, out[-4000:]

    def retrain(self, rebuild_dataset: bool = True) -> dict:
        """Полный цикл переобучения. Возвращает статус, метрики, путь к архиву."""
        self.log_action("retrain_started", rebuild_dataset=rebuild_dataset)

        if rebuild_dataset:
            ok, log_build = self._run("scripts/build_dataset.py")
            if not ok:
                self.log_action("retrain_failed", stage="build_dataset")
                return {"ok": False, "stage": "build_dataset", "log": log_build}

        ok, log_train = self._run("models/text_classifier.py")
        if not ok:
            self.log_action("retrain_failed", stage="train")
            return {"ok": False, "stage": "train", "log": log_train}

        # версионируем веса
        archived = None
        if WEIGHTS.exists():
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            archived = ARCHIVE_DIR / f"text_classifier_{ts}.joblib"
            shutil.copy2(WEIGHTS, archived)

        metrics = {}
        if METRICS.exists():
            try:
                metrics = json.loads(METRICS.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                metrics = {}

        result = {
            "ok": True,
            "archived_weights": str(archived) if archived else None,
            "accuracy": metrics.get("accuracy"),
            "macro_f1": (metrics.get("macro avg") or {}).get("f1-score"),
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }
        self.log_action("retrain_done", **{k: result[k] for k in ("accuracy", "macro_f1", "archived_weights")})
        return result
