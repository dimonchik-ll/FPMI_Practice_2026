from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LEVEL_PATHS: dict[int, Path] = {
    1: PROJECT_ROOT / "assets" / "maps" / "level-1.tmx",
    2: PROJECT_ROOT / "assets" / "maps" / "level-2.tmx",
}


def get_level_path(level_number: int) -> Path:
    try:
        return LEVEL_PATHS[level_number]
    except KeyError as error:
        available_levels = ", ".join(map(str, sorted(LEVEL_PATHS)))

        raise ValueError(
            f"Уровень {level_number} не найден. "
            f"Доступные уровни: {available_levels}."
        ) from error