from pathlib import Path

from .player import Player


def play_sound(file_path: Path):
    Player.play_file(file_path)


def format_time(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    result = f"{minutes:02d}:{seconds:02d}"
    if hours > 0:
        result = f"{hours:02d}:{result}"
    return result
