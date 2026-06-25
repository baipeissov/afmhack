"""
Прогоняет pipeline.live_stream.analyze_chunks() заранее (до сцены) и
сохраняет результат в JSON. На сцене считать заново не нужно — chunks.json
просто проигрывается scripts/replay_live.py с реальными задержками между
чанками, имитируя живой эфир без риска не успеть в 5-минутный слот.

Запуск:
    python scripts/precompute_live_chunks.py path/to/video.mp4
    python scripts/precompute_live_chunks.py path/to/video.mp4 --chunk-seconds 30 --out data/live_demo.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import live_stream  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path")
    parser.add_argument("--chunk-seconds", type=int, default=live_stream.DEFAULT_CHUNK_SECONDS)
    parser.add_argument("--out", default="data/live_chunks_precomputed.json")
    args = parser.parse_args()

    print(f"Считаю чанки по {args.chunk_seconds} сек для {args.video_path} ...")
    results = list(live_stream.analyze_chunks(args.video_path, chunk_seconds=args.chunk_seconds))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"chunk_seconds": args.chunk_seconds, "results": results}, f, ensure_ascii=False, indent=2)

    print(f"Готово: {len(results)} чанков сохранено в {out_path}")
    for r in results:
        d = r["dossier"]
        print(f"  [t+{r['stream_offset_seconds']}s] чанк {r['chunk_index']}: risk={d['risk_score']:.2f} ({d['risk_level']})")


if __name__ == "__main__":
    main()
