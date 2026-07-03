from __future__ import annotations

from pathlib import Path
from typing import Any

_IMAGE_CACHE: dict[tuple[Path, tuple[int, int] | None], Any] = {}


def load_image(path: Path, size: tuple[int, int] | None = None) -> Any | None:
    key = (path, size)
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]
    if not path.exists():
        return None

    import pygame

    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        return None

    if size is not None and image.get_size() != size:
        image = pygame.transform.scale(image, size)
    _IMAGE_CACHE[key] = image
    return image


def load_sprite_frame(
    path: Path,
    frame_index: int,
    frame_size: tuple[int, int],
    target_size: tuple[int, int] | None = None,
) -> Any | None:
    sheet = load_image(path)
    if sheet is None:
        return None

    import pygame

    frame_width, frame_height = frame_size
    columns = max(1, sheet.get_width() // frame_width)
    index = frame_index % columns
    rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
    if not sheet.get_rect().contains(rect):
        return None
    frame = sheet.subsurface(rect).copy()
    if target_size is not None and frame.get_size() != target_size:
        frame = pygame.transform.scale(frame, target_size)
    return frame


def clear_cache() -> None:
    _IMAGE_CACHE.clear()
