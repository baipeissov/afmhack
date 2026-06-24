# AI Media Watch — детектор нелегальных казино, финансовых пирамид и мошенничества в видео из соцсетей

MVP для хакатона АФМ AI Hackathon 2026, трек "AI Media Watch".

## Идея

Видео (загруженный файл или ссылка на уже скачанный ролик) → извлечение признаков из всех
модальностей (речь, текст на экране, визуальный ряд, метаданные аккаунта) → **собственная**
fusion-модель → объяснимый risk score (0–1) → приоритизированная очередь для аналитика-человека.

Решение НЕ обращается к внешним LLM API. Классификатор текста и fusion-модель — обучены нами
локально на собственных весах (см. `models/`).

## Архитектура

```
INPUT (file/URL)
   │
   ├─ pipeline/audio.py     → ffmpeg + Whisper        → транскрипт с таймкодами
   ├─ pipeline/ocr.py       → ffmpeg + PaddleOCR       → текст на экране с таймкодами
   ├─ pipeline/visual.py    → CLIP zero-shot           → визуальные маркеры (казино, скрины дохода и т.п.)
   └─ pipeline/metadata.py  → heuristics                → возраст аккаунта, рост подписчиков, реф-ссылка
   │
   ▼
models/predict_text.py  (Component A: fine-tuned e5-base classifier, 6 классов)
   применяется к транскрипту И к OCR-тексту
   │
   ▼
models/fusion_predict.py (Component B: LogisticRegression на признаках всех модальностей)
   │
   ▼
api/main.py → JSON-досье: risk_score, класс, evidence[] с таймкодами, RU-объяснение, рекомендация
   │
   ▼
frontend/ → очередь по риску → карточка кейса → approve/reject/request-review (human-in-the-loop)
```

Сбор данных из TikTok/Instagram в проде представлен как **pluggable-коннектор** через официальные
API (TikTok Research API, Instagram Graph API) + жалобы граждан — в демо это не реализуется
(нет лайв-скрейпинга, нет авто-отправки в органы, нет имитации действий человека).

## Схема классов (общая для текстового классификатора и fusion-объяснений)

| id | класс                  | описание                                              |
|----|------------------------|--------------------------------------------------------|
| 0  | clean                  | обычный/нейтральный контент                            |
| 1  | casino_betting         | нелегальное онлайн-казино / ставки                      |
| 2  | pyramid_investment     | гарантированный доход / финансовая пирамида             |
| 3  | referral_network       | реферальная/сетевая схема                                |
| 4  | urgency_pressure       | психологическое давление / срочность                    |
| 5  | hidden_engagement      | "напиши +", закрытый канал, призыв в личку              |

## Структура репозитория

```
data/        датасеты, схема маппинга, seed-файлы, шаблон лейблов для видео
models/      обучение и сохранённые веса Component A и Component B
pipeline/    экстракторы признаков по модальностям (audio/ocr/visual/metadata)
api/         FastAPI-сервис (POST /analyze, GET /queue)
frontend/    дашборд аналитика
scripts/     сборка датасета, демо-прогон
```

## Запуск (план)

```bash
pip install -r requirements.txt
python scripts/build_dataset.py        # Layer 1 (HF datasets) + seed (Layer 2) -> data/train.csv
python models/text_classifier.py       # обучение Component A
python models/train_fusion.py          # обучение Component B
uvicorn api.main:app --reload          # API
```

Всё считается на CPU, без сети на сцене (модели и веса локальные, демо-видео закэшированы заранее
в `scripts/run_demo.py`).
# afmhack
