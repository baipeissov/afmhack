"""
Демо-скрипт для сцены: НЕ зависит от сети/Collector'а/фронтенда. Берёт
локальный путь к видео (заранее закэшированному, см. README "Демо без сети"),
прогоняет полный pipeline и печатает готовое досье в консоль.

Запуск:
    python scripts/run_demo.py path/to/video.mp4
    python scripts/run_demo.py path/to/video.mp4 --age-days 23 --growth 12 --referral
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.dossier import build_dossier  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path")
    parser.add_argument("--age-days", type=float, default=365)
    parser.add_argument("--growth", type=float, default=0.0)
    parser.add_argument("--referral", action="store_true")
    args = parser.parse_args()

    account_metadata = {
        "account_age_days": args.age_days,
        "follower_growth": args.growth,
        "referral_link_in_bio": args.referral,
    }

    print(f"Анализирую {args.video_path} ...\n")
    dossier = build_dossier(args.video_path, account_metadata)

    print("=" * 60)
    print(f"RISK: {dossier['risk_score']:.2f} — {dossier['risk_level']} | Класс: {dossier['top_class_ru']}")
    print("=" * 60)
    for line in dossier["explanations"]:
        print(line)
    if not dossier["explanations"]:
        print("(явных маркеров не найдено)")
    print()
    print(f"→ Рекомендация: {dossier['recommendation']}")
    print()
    print("Вклад признаков в risk score (объяснимость fusion-модели):")
    for name, contrib in sorted(dossier["contributions"].items(), key=lambda kv: -abs(kv[1])):
        print(f"   {name:32s} {contrib:+.3f}")


if __name__ == "__main__":
    main()
