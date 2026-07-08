from __future__ import annotations

from typing import Any

from shared.contracts import EnemyKind, Vector2

from enemies.tuning import (
    BOSS_SHADOW_HEIGHT,
    BOSS_SHADOW_WIDTH,
    BOSS_TARGET_DRAW_SIZE,
    ENEMY_SHADOW_COLOR,
    ENEMY_SHADOW_HEIGHT,
    ENEMY_SHADOW_WIDTH,
    ENEMY_TARGET_DRAW_SIZE,
    HEALTH_BAR_BACKGROUND_COLOR,
    HEALTH_BAR_BORDER_COLOR,
    HEALTH_BAR_FILL_COLOR,
    HEALTH_BAR_HEIGHT,
    HEALTH_BAR_INNER_PADDING,
    HEALTH_BAR_LOW_FILL_COLOR,
    HEALTH_BAR_OFFSET_Y,
    HEALTH_BAR_OUTLINE_COLOR,
    HEALTH_BAR_WIDTH,
    SHADOW_OFFSET_Y,
)


BOSS_LIKE_KINDS = {
    EnemyKind.ENEMY_4,
}


def target_draw_size_for_kind(kind: EnemyKind) -> int:
    if kind in BOSS_LIKE_KINDS:
        return BOSS_TARGET_DRAW_SIZE

    return ENEMY_TARGET_DRAW_SIZE


def screen_center(
    position: Vector2,
    camera_offset: Vector2,
) -> tuple[int, int]:
    return (
        int(round(position.x - camera_offset.x)),
        int(round(position.y - camera_offset.y)),
    )


def draw_enemy_shadow(
    surface: Any,
    center: tuple[int, int],
    kind: EnemyKind,
) -> None:
    import pygame

    if kind in BOSS_LIKE_KINDS:
        width = BOSS_SHADOW_WIDTH
        height = BOSS_SHADOW_HEIGHT
    else:
        width = ENEMY_SHADOW_WIDTH
        height = ENEMY_SHADOW_HEIGHT

    shadow_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow_surface,
        ENEMY_SHADOW_COLOR,
        shadow_surface.get_rect(),
    )

    surface.blit(
        shadow_surface,
        (
            center[0] - width // 2,
            center[1] + SHADOW_OFFSET_Y - height // 2,
        ),
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

    outline = pygame.Rect(
        center[0] - HEALTH_BAR_WIDTH // 2 - 1,
        center[1] - HEALTH_BAR_OFFSET_Y - 1,
        HEALTH_BAR_WIDTH + 2,
        HEALTH_BAR_HEIGHT + 2,
    )
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

    pygame.draw.rect(surface, HEALTH_BAR_OUTLINE_COLOR, outline, border_radius=3)
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
