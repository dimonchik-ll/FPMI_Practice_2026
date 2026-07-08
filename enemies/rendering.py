from __future__ import annotations

from typing import Any

from shared.contracts import Vector2

from enemies.tuning import (
    HEALTH_BAR_BACKGROUND_COLOR,
    HEALTH_BAR_BORDER_COLOR,
    HEALTH_BAR_FILL_COLOR,
    HEALTH_BAR_HEIGHT,
    HEALTH_BAR_INNER_PADDING,
    HEALTH_BAR_LOW_FILL_COLOR,
    HEALTH_BAR_OFFSET_Y,
    HEALTH_BAR_WIDTH,
)


def screen_center(
    position: Vector2,
    camera_offset: Vector2,
) -> tuple[int, int]:
    return (
        int(round(position.x - camera_offset.x)),
        int(round(position.y - camera_offset.y)),
    )


def draw_health_bar(
    surface: Any,
    center: tuple[int, int],
    health: int,
    max_health: int,
) -> None:
    import pygame

    if max_health <= 0:
        return

    ratio = max(0.0, min(1.0, health / max_health))

    outer = pygame.Rect(
        center[0] - HEALTH_BAR_WIDTH // 2,
        center[1] - HEALTH_BAR_OFFSET_Y,
        HEALTH_BAR_WIDTH,
        HEALTH_BAR_HEIGHT,
    )
    inner = outer.inflate(
        -HEALTH_BAR_INNER_PADDING * 2,
        -HEALTH_BAR_INNER_PADDING * 2,
    )

    fill_width = int(inner.width * ratio)
    fill_color = (
        HEALTH_BAR_LOW_FILL_COLOR
        if ratio <= 0.30
        else HEALTH_BAR_FILL_COLOR
    )

    pygame.draw.rect(surface, HEALTH_BAR_BORDER_COLOR, outer, border_radius=2)
    pygame.draw.rect(surface, HEALTH_BAR_BACKGROUND_COLOR, inner, border_radius=1)

    if fill_width > 0:
        pygame.draw.rect(
            surface,
            fill_color,
            (
                inner.x,
                inner.y,
                fill_width,
                inner.height,
            ),
            border_radius=1,
        )
