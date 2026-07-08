from shared.contracts import EnemyKind, Vector2

from enemies.rendering import screen_center, target_draw_size_for_kind
from enemies.tuning import (
    BOSS_TARGET_DRAW_SIZE,
    ENEMY_TARGET_DRAW_SIZE,
    HEALTH_BAR_HEIGHT,
    HEALTH_BAR_WIDTH,
)


def test_screen_center_respects_camera_offset() -> None:
    assert screen_center(
        Vector2(100.4, 50.6),
        Vector2(10.0, 5.0),
    ) == (90, 46)


def test_boss_uses_larger_draw_size() -> None:
    assert target_draw_size_for_kind(EnemyKind.ENEMY_4) == BOSS_TARGET_DRAW_SIZE
    assert target_draw_size_for_kind(EnemyKind.ENEMY_1) == ENEMY_TARGET_DRAW_SIZE


def test_health_bar_has_readable_dimensions() -> None:
    assert HEALTH_BAR_WIDTH >= 40
    assert HEALTH_BAR_HEIGHT >= 7
