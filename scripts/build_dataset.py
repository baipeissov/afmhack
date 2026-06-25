"""
Сборка train.csv для Component A (Fraud Text Classifier).

Layer 1 — заимствованные датасеты (объём + базовый сигнал "это спам/скам"),
переразмечаются в нашу 6-классовую схему (см. data/label_schema.py).
Layer 2 — data/seed_kz_ru.csv, наша ручная разметка RU/KZ — главный
дифференциатор для критерия "собственная модель".

Каждый источник скачивается через `datasets`. Если источник гейтнут (нужен
HF login + accept license) или скрипт датасета требует remote code — мы НЕ
падаем, а пишем warning и идём дальше (см. ROADMAP пункт про
ruSpamModels/russian-spam-detection и redasers/difraud).

Выход: data/train.csv с колонками [text, label, source, lang]
  label — int id из data/label_schema.LABELS
"""

import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.label_schema import LABELS  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUT_PATH = DATA_DIR / "train.csv"


def _df(text, label, source, lang):
    return pd.DataFrame({"text": text, "label": label, "source": source, "lang": lang})


# ---------------------------------------------------------------------------
# Per-source loaders. Each returns a DataFrame[text, label, source, lang] or
# None if the source could not be loaded (auth/gating/schema mismatch).
# ---------------------------------------------------------------------------

def load_difraud():
    """
    redasers/difraud — мирор DIFrauD. `load_dataset(name)` не работает:
    HF больше не поддерживает loading-script датасеты ("Dataset scripts are
    no longer supported"), поэтому читаем jsonl-файлы прямо из репозитория
    через huggingface_hub.hf_hub_download (никакого remote code).

    Репозиторий разбит на категории-подпапки, каждая — СВОЙ бинарный
    classification task (1 = целевой класс категории, 0 = легитимный
    пример из того же домена, т.е. hard negative):
      job_scams/    1 = вакансия-обманка       -> у нас класс 2 (pyramid_investment:
                                                   классическая схема "лёгкие деньги без опыта")
      phishing/     1 = фишинговое письмо      -> класс 5 (hidden_engagement:
                                                   просят перейти/заполнить форму/ответить)
      sms/          1 = SMS-скам/спам          -> класс 5 (hidden_engagement:
                                                   "txt CODE to NNNNN", прямой призыв к действию)
    label==0 внутри каждой из этих категорий — легитимный пример того же
    домена, берём как clean (0): хорошие hard negatives для классификатора.

    fake_news/, political_statements/, product_reviews/, twitter_rumours/ —
    вне нашей схемы (не финансовое мошенничество), не используются.
    """
    name = "redasers/difraud"
    CATEGORY_TO_CLASS = {
        "job_scams": 2,
        "phishing": 5,
        "sms": 5,
    }

    try:
        from huggingface_hub import hf_hub_download
        import json
    except Exception as e:  # noqa: BLE001
        warnings.warn(f"[skip] {name}: {e}")
        return None

    texts, labels = [], []
    for category, target_class in CATEGORY_TO_CLASS.items():
        try:
            path = hf_hub_download(name, f"{category}/train.jsonl", repo_type="dataset")
            with open(path, encoding="utf-8") as f:
                rows = [json.loads(line) for line in f]
        except Exception as e:  # noqa: BLE001
            warnings.warn(f"[skip] {name}/{category}: {e}")
            continue

        for r in rows:
            texts.append(r["text"])
            labels.append(target_class if int(r["label"]) == 1 else 0)

    if not texts:
        return None
    return _df(texts, labels, source=name, lang="en")


def load_all_scam_spam():
    """
    FredZhang7/all-scam-spam — бинарный spam/ham, в основном EN.
    spam -> 5 (скрытое вовлечение / общее навязчивое предложение),
    ham   -> 0 (clean).
    Это грубая аппроксимация: бинарный спам не несёт тонкой семантики наших
    4 "финансовых" классов, поэтому этот источник даёт объём для границы
    clean/not-clean, а тонкая разметка остаётся на seed-данных (Layer 2).
    """
    name = "FredZhang7/all-scam-spam"
    try:
        from datasets import load_dataset

        ds = load_dataset(name, split="train")
    except Exception as e:  # noqa: BLE001
        warnings.warn(f"[skip] {name}: {e}")
        return None

    cols = ds.column_names
    text_col = "text" if "text" in cols else cols[0]
    label_col = next((c for c in ("is_spam", "label") if c in cols), None)
    if label_col is None:
        warnings.warn(f"[skip] {name}: no label column found in {cols}")
        return None

    labels = [5 if int(r[label_col]) == 1 else 0 for r in ds]
    return _df(ds[text_col], labels, source=name, lang="en")


def load_spam_messages():
    """
    mshenoda/spam-messages (~59k, включает Telegram-спам).
    spam -> 5 (скрытое вовлечение), ham/clean -> 0.
    """
    name = "mshenoda/spam-messages"
    try:
        from datasets import load_dataset

        ds = load_dataset(name, split="train")
    except Exception as e:  # noqa: BLE001
        warnings.warn(f"[skip] {name}: {e}")
        return None

    cols = ds.column_names
    text_col = "text" if "text" in cols else cols[0]
    label_col = next((c for c in ("label", "is_spam") if c in cols), None)
    if label_col is None:
        warnings.warn(f"[skip] {name}: no label column found in {cols}")
        return None

    def to_class(v):
        # допускаем как int 0/1, так и строки "spam"/"ham"
        s = str(v).strip().lower()
        if s in ("1", "spam", "true"):
            return 5
        return 0

    labels = [to_class(r[label_col]) for r in ds]
    return _df(ds[text_col], labels, source=name, lang="en")


def load_ru_spam_models():
    """
    ruSpamModels/russian-spam-detection — RU, gated (cc-by-nc-4.0, нужен
    HF login + accept license). Если токена/доступа нет — пропускаем с
    warning, не роняем сборку.
    spam -> 5, ham -> 0.
    """
    name = "ruSpamModels/russian-spam-detection"
    try:
        from datasets import load_dataset

        ds = load_dataset(name, split="train")
    except Exception as e:  # noqa: BLE001
        warnings.warn(
            f"[skip] {name}: {e}\n"
            "  -> вероятно gated dataset: выполните `huggingface-cli login` и "
            "примите лицензию на странице датасета, затем повторите запуск."
        )
        return None

    cols = ds.column_names
    text_col = "text" if "text" in cols else cols[0]
    label_col = next((c for c in ("label", "is_spam") if c in cols), None)
    if label_col is None:
        warnings.warn(f"[skip] {name}: no label column found in {cols}")
        return None

    labels = [5 if int(r[label_col]) == 1 else 0 for r in ds]
    return _df(ds[text_col], labels, source=name, lang="ru")


def load_russian_inappropriate():
    """
    NiGuLa/Russian_Inappropriate_Messages — RU, ~125k. ВАЖНО: 'inappropriate'
    это не бинарная метка, а вероятностный score [0,1] (доля разметчиков,
    посчитавших фразу токсичной). Берём ТОЛЬКО низкий score (< 0.1, явно
    нетоксичные) как доп. источник класса 0 (clean) на русском —
    токсичность сама по себе не относится к нашей схеме мошенничества,
    нам важен только объём естественного RU-текста без скам-сигнала.
    """
    name = "NiGuLa/Russian_Inappropriate_Messages"
    try:
        from datasets import load_dataset

        ds = load_dataset(name, split="train")
    except Exception as e:  # noqa: BLE001
        warnings.warn(f"[skip] {name}: {e}")
        return None

    cols = ds.column_names
    text_col = "text" if "text" in cols else cols[0]
    if "inappropriate" not in cols:
        warnings.warn(f"[skip] {name}: no 'inappropriate' column found in {cols}")
        return None

    clean_rows = [r for r in ds if float(r["inappropriate"]) < 0.1]
    if not clean_rows:
        warnings.warn(f"[skip] {name}: no clean (score<0.1) rows found")
        return None

    texts = [r[text_col] for r in clean_rows]
    labels = [0] * len(texts)
    return _df(texts, labels, source=name, lang="ru")


def load_seed():
    """Layer 2 — наша ручная разметка RU/KZ. Это файл, который команда
    дополняет руками; обязателен для итоговой модели."""
    path = DATA_DIR / "seed_kz_ru.csv"
    if not path.exists():
        warnings.warn(f"[skip] seed file not found: {path}")
        return None
    df = pd.read_csv(path)
    df["source"] = "seed_kz_ru"
    return df[["text", "label", "source", "lang"]]


def load_synthetic():
    """Layer 3 — шаблонная синтетика RU/KZ (scripts/generate_synthetic.py).
    Закрывает дыру в данных: casino_betting/referral_network/urgency_pressure
    почти не встречаются в Layer-1, а pyramid_investment/hidden_engagement
    там почти все на английском."""
    path = DATA_DIR / "synthetic_seed.csv"
    if not path.exists():
        warnings.warn(
            f"[skip] synthetic file not found: {path} "
            "-> запустите scripts/generate_synthetic.py"
        )
        return None
    df = pd.read_csv(path)
    df["source"] = "synthetic_template"
    return df[["text", "label", "source", "lang"]]


def load_confirmed_cases():
    """Layer 4 — подтверждённые аналитиком кейсы (цикл самообучения).
    DatasetCuratorAgent дописывает сюда текстовые сигналы (транскрипт+OCR)
    кейсов, которые аналитик подтвердил как мошеннические. Это реальные
    RU/KZ примеры из продакшена — ценнейший сигнал, поэтому в OWN_SOURCES
    (не каппится). См. agents/dataset/curator.py."""
    path = DATA_DIR / "curated_labeled.csv"
    if not path.exists():
        warnings.warn(f"[skip] confirmed-cases file not found: {path}")
        return None
    df = pd.read_csv(path)
    df["source"] = "confirmed_case"
    return df[["text", "label", "source", "lang"]]


# Классы 0 (clean) и 5 (hidden_engagement) получают на порядки больше строк
# из Layer 1, чем остальные. Без ограничения сверху train.csv был бы на 95%
# из них, и embedding-обучение Component A тратило бы время в основном на
# переобучение по доминирующим классам. Ограничиваем сверху, не трогая
# редкие классы (1-4), где каждая строка на счету.
#
# ВАЖНО: кап применяется ТОЛЬКО к внешним (Layer 1) источникам, а не к нашим
# seed_kz_ru/synthetic_template. Урок с первого прогона: если капать весь
# label целиком, наши ~19 RU/KZ-примеров для hidden_engagement тонут в 8000
# строк англоязычного spam/phishing — модель в итоге не распознаёт короткие
# RU-фразы вида "напиши + в директ" (это другое распределение текста, чем
# многостраничные английские фишинг-письма), даже если сами эти строки были
# в train split. Поэтому ограничиваем именно внешний объём, а наш Layer 2/3
# остаётся в полном объёме и составляет заметную долю класса.
MAX_EXTERNAL_PER_LABEL = {0: 2500, 5: 250}
OWN_SOURCES = {"seed_kz_ru", "synthetic_template", "confirmed_case"}

LOADERS = [
    load_difraud,
    load_all_scam_spam,
    load_spam_messages,
    load_ru_spam_models,
    load_russian_inappropriate,
    load_seed,
    load_synthetic,
    load_confirmed_cases,
]


def main():
    frames = []
    for loader in LOADERS:
        print(f"==> {loader.__name__}")
        df = loader()
        if df is None:
            continue
        before = len(df)
        df = df.dropna(subset=["text", "label"])
        df["label"] = df["label"].astype(int)
        df = df[df["label"].isin(LABELS.keys())]
        print(f"    loaded {before} rows, kept {len(df)} after cleaning")
        frames.append(df)

    if not frames:
        print("Нет ни одного загруженного источника. Проверьте сеть/доступы.")
        sys.exit(1)

    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["text"])

    capped = []
    for label, group in out.groupby("label"):
        cap = MAX_EXTERNAL_PER_LABEL.get(label)
        if cap is None:
            capped.append(group)
            continue
        own = group[group["source"].isin(OWN_SOURCES)]
        external = group[~group["source"].isin(OWN_SOURCES)]
        if len(external) > cap:
            external = external.sample(n=cap, random_state=42)
        capped.append(pd.concat([own, external], ignore_index=True))
    out = pd.concat(capped, ignore_index=True)

    out.to_csv(OUT_PATH, index=False)

    print(f"\nИтого: {len(out)} строк -> {OUT_PATH}")
    print(out.groupby(["label", "source"]).size())


if __name__ == "__main__":
    main()
