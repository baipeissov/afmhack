# AI Media Watch — детектор нелегальных казино, финансовых пирамид и мошенничества в видео из соцсетей

MVP для хакатона АФМ AI Hackathon 2026, трек "AI Media Watch".

## Идея

Видео (загруженный файл или ссылка на уже скачанный ролик) → извлечение признаков из всех
модальностей (речь, текст на экране, визуальный ряд, метаданные аккаунта) → **собственная**
fusion-модель → объяснимый risk score (0–1) → приоритизированная очередь для аналитика-человека.

Решение НЕ обращается к внешним LLM API. Классификатор текста и fusion-модель — обучены нами
локально на собственных весах (см. `models/`).

## Архитектура

Запускается один раз (`python scripts/run_collector.py`) и работает непрерывно — без ручного
аплоада видео на каждый кейс. Сбор на постоянной основе обязателен по регламенту хакатона.

```
Collector (run_collector.py) — опрашивает источники по таймеру
   ├─ pipeline/connectors/tiktok_connector.py     → публичные TikTok-хэштеги (yt-dlp, без логина)
   ├─ pipeline/connectors/instagram_connector.py  → публичные Instagram-URL (watchlist/жалобы)
   └─ pipeline/connectors/citizen_reports.py      → очередь жалоб граждан (POST /report)
   │  (в проде сюда же подключается официальный TikTok Research API / Instagram Graph API —
   │   тот же интерфейс Connector.poll(), просто другая реализация после approval ключей)
   ▼
НОВОЕ видео обнаружено → автоматически в pipeline, без участия человека
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
risk_queue → JSON-досье: risk_score, класс, evidence[] с таймкодами, RU-объяснение, рекомендация
   │
   ▼
frontend/ → очередь по риску → карточка кейса → approve/reject/request-review (human-in-the-loop)
```

Этический периметр сбора (критично для защиты перед регулятором):
- читаем только **публичный** контент (хэштег-страницы, публичные посты, жалобы граждан) —
  никакого логина, обхода капч/антибота или имитации человека;
- не собираем PII сверх того, что уже публично (публичный @handle, caption, видео) —
  никаких подписчиков, переписок, геолокации;
- частота и объём опроса намеренно ограничены (rate-limited monitoring, не массовый краулинг);
- человек подтверждает любое действие по кейсу — система НИЧЕГО не отправляет в органы сама.

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
src/         дашборд аналитика (Next.js, см. ниже)
scripts/     сборка датасета, демо-прогон
```

## Запуск backend (план)

```bash
pip install -r requirements.txt
python scripts/build_dataset.py        # Layer 1 (HF datasets) + seed (Layer 2) + synthetic (Layer 3) -> data/train.csv
python models/text_classifier.py       # обучение Component A
python models/train_fusion.py          # обучение Component B
uvicorn api.main:app --reload          # API + дашборд
python scripts/run_collector.py        # запустить один раз — дальше сбор и анализ идут сами
```

## Frontend (`src/`, корень репозитория)

Next.js (App Router) + TypeScript + Tailwind CSS.

```bash
npm install
npm run dev      # dev server → http://localhost:3000
npm run build    # production build
npm run start    # serve the production build
npm run lint     # eslint
```

```
src/app/
  layout.tsx     # root layout
  page.tsx       # home page
  globals.css    # Tailwind + global styles
public/          # static assets
```
