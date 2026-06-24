"""Единая точка получения пути к ffmpeg-бинарнику. На машинах без Homebrew/
системного ffmpeg используем portable-бинарник из imageio-ffmpeg — это и
проще для жюри (никаких системных зависимостей, только pip install)."""

import shutil


def get_ffmpeg_path() -> str:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()
