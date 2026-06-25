"""
Проигрывает заранее посчитанные чанки (см. precompute_live_chunks.py) в
очередь /queue с реальными задержками между ними — для зрителя на сцене
выглядит как живой анализ прямого эфира (дашборд сам обновится при
следующем опросе GET /queue), но без риска не успеть в реальном времени:
вся тяжёлая работа (Whisper/OCR/CLIP/LLM) уже сделана заранее.

Запуск (бэкенд должен быть поднят, чтобы дашборд видел очередь):
    python scripts/replay_live.py data/live_chunks_precomputed.json
    python scripts/replay_live.py data/live_chunks_precomputed.json --delay-seconds 8 --no-initial-wait
"""

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.main import _dossier_to_queue_record, _read_queue, _write_queue  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("chunks_json")
    parser.add_argument("--account-handle", default=None)
    parser.add_argument("--platform", default="TikTok")
    parser.add_argument(
        "--delay-seconds", type=float, default=None,
        help="интервал между чанками (по умолчанию = chunk_seconds из файла, т.е. реальный темп эфира)",
    )
    parser.add_argument("--no-initial-wait", action="store_true", help="не ждать перед первым чанком")
    args = parser.parse_args()

    with open(args.chunks_json, encoding="utf-8") as f:
        data = json.load(f)
    chunk_seconds = data["chunk_seconds"]
    delay = args.delay_seconds if args.delay_seconds is not None else chunk_seconds

    session_id = f"live_{uuid.uuid4().hex[:8]}"
    print(f"Live-сессия {session_id}: {len(data['results'])} чанков, интервал {delay:.0f}с")

    for i, result in enumerate(data["results"]):
        if i > 0 or not args.no_initial_wait:
            time.sleep(delay)

        item_id = f"{session_id}_chunk{result['chunk_index']:03d}"
        record = _dossier_to_queue_record(
            result["dossier"], item_id, source="live_stream",
            account_handle=args.account_handle, platform=args.platform,
        )
        record["stream_offset_seconds"] = result["stream_offset_seconds"]
        record["live_session_id"] = session_id

        items = _read_queue()
        items.append(record)
        _write_queue(items)

        d = result["dossier"]
        print(
            f"[t+{result['stream_offset_seconds']}s] чанк {result['chunk_index']} → /queue: "
            f"risk={d['risk_score']:.2f} ({d['risk_level']}) — {d['top_class_ru']}"
        )

    print("Эфир завершён.")


if __name__ == "__main__":
    main()
