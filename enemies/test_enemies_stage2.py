from __future__ import annotations

from enemies.api import (
    ENEMY_DISPLAY_NAMES,
    MAX_ACTIVE_ENEMIES,
    MAX_ENDLESS_SPEED_MULTIPLIER,
    MIN_SPAWN_INTERVAL,
    EnemySystem,
    Facing,
    WAVE_PLANS,
    wave_plan_for,
    wave_settings_for,
)
from shared.asset_manifest import ENEMY_WALK_SHEETS
from shared.contracts import EnemyKind, GameEventKind, Vector2


def start_single_enemy(
    monkeypatch,
    route: tuple[Vector2, ...],
) -> EnemySystem:
    monkeypatch.setitem(WAVE_PLANS, 99, (EnemyKind.ENEMY_1,))

    enemies = EnemySystem()

    assert enemies.start_wave(99, route)
    enemies.update(0.0)

    return enemies


def test_every_enemy_has_display_name() -> None:
    assert set(ENEMY_DISPLAY_NAMES) == set(EnemyKind)


def test_enemy_faces_right_on_rightward_segment(monkeypatch) -> None:
    enemies = start_single_enemy(
        monkeypatch,
        (
            Vector2(0, 0),
            Vector2(100, 0),
        ),
    )

    assert enemies._enemies[0].facing == Facing.RIGHT


def test_enemy_faces_left_on_leftward_segment(monkeypatch) -> None:
    enemies = start_single_enemy(
        monkeypatch,
        (
            Vector2(100, 0),
            Vector2(0, 0),
        ),
    )

    assert enemies._enemies[0].facing == Facing.LEFT


def test_enemy_faces_down_on_downward_segment(monkeypatch) -> None:
    enemies = start_single_enemy(
        monkeypatch,
        (
            Vector2(0, 0),
            Vector2(0, 100),
        ),
    )

    assert enemies._enemies[0].facing == Facing.DOWN


def test_enemy_faces_up_on_upward_segment(monkeypatch) -> None:
    enemies = start_single_enemy(
        monkeypatch,
        (
            Vector2(0, 100),
            Vector2(0, 0),
        ),
    )

    assert enemies._enemies[0].facing == Facing.UP


def test_enemy_changes_facing_at_corner(monkeypatch) -> None:
    enemies = start_single_enemy(
        monkeypatch,
        (
            Vector2(0, 0),
            Vector2(10, 0),
            Vector2(10, 100),
        ),
    )

    assert enemies._enemies[0].facing == Facing.RIGHT

    enemies.update(0.2)

    assert enemies._enemies[0].facing == Facing.DOWN


def test_enemy_reaches_goal_after_multiple_turns(monkeypatch) -> None:
    enemies = start_single_enemy(
        monkeypatch,
        (
            Vector2(0, 0),
            Vector2(80, 0),
            Vector2(80, 80),
            Vector2(0, 80),
            Vector2(0, 0),
        ),
    )

    events = []

    for _ in range(80):
        events.extend(enemies.update(0.1))

    assert any(
        event.kind == GameEventKind.ENEMY_REACHED_GOAL
        for event in events
    )


def test_side_sheet_is_not_flipped_for_left_facing(
    monkeypatch,
    tmp_path,
) -> None:
    down_walk = tmp_path / "down_walk.png"
    side_walk = tmp_path / "side_walk.png"

    down_walk.touch()
    side_walk.touch()

    monkeypatch.setitem(
        ENEMY_WALK_SHEETS,
        EnemyKind.ENEMY_1,
        down_walk,
    )

    enemies = start_single_enemy(
        monkeypatch,
        (
            Vector2(0, 0),
            Vector2(-100, 0),
        ),
    )

    runtime_enemy = enemies._enemies[0]
    runtime_enemy.facing = Facing.LEFT

    selection = enemies._animation_selection(runtime_enemy)

    assert selection.path == side_walk
    assert not selection.flip_horizontal


def test_side_sheet_is_flipped_for_right_facing(
    monkeypatch,
    tmp_path,
) -> None:
    down_walk = tmp_path / "down_walk.png"
    side_walk = tmp_path / "side_walk.png"

    down_walk.touch()
    side_walk.touch()

    monkeypatch.setitem(
        ENEMY_WALK_SHEETS,
        EnemyKind.ENEMY_1,
        down_walk,
    )

    enemies = start_single_enemy(
        monkeypatch,
        (
            Vector2(0, 0),
            Vector2(100, 0),
        ),
    )

    runtime_enemy = enemies._enemies[0]
    runtime_enemy.facing = Facing.RIGHT

    selection = enemies._animation_selection(runtime_enemy)

    assert selection.path == side_walk
    assert selection.flip_horizontal


def test_wave_five_ten_and_twenty_are_created() -> None:
    assert len(wave_plan_for(5)) > 0
    assert len(wave_plan_for(10)) > 0
    assert len(wave_plan_for(20)) > 0


def test_endless_waves_increase_enemy_count() -> None:
    assert len(wave_plan_for(5)) < len(wave_plan_for(10))
    assert len(wave_plan_for(10)) < len(wave_plan_for(20))


def test_endless_waves_increase_health() -> None:
    assert (
        wave_settings_for(5).health_multiplier
        < wave_settings_for(10).health_multiplier
    )
    assert (
        wave_settings_for(10).health_multiplier
        < wave_settings_for(20).health_multiplier
    )


def test_endless_speed_has_upper_limit() -> None:
    assert (
        wave_settings_for(10_000).speed_multiplier
        == MAX_ENDLESS_SPEED_MULTIPLIER
    )


def test_spawn_interval_has_lower_limit() -> None:
    assert (
        wave_settings_for(10_000).spawn_interval
        == MIN_SPAWN_INTERVAL
    )


def test_active_enemy_count_is_limited(monkeypatch) -> None:
    monkeypatch.setitem(
        WAVE_PLANS,
        77,
        (EnemyKind.ENEMY_1,) * 100,
    )

    enemies = EnemySystem()

    assert enemies.start_wave(
        77,
        (
            Vector2(0, 0),
            Vector2(1_000_000, 0),
        ),
    )

    for _ in range(20):
        enemies.update(1.0)

    assert len(enemies._enemies) <= MAX_ACTIVE_ENEMIES


def test_camera_offset_changes_screen_position_only() -> None:
    world_position = Vector2(200, 150)
    camera_offset = Vector2(60, 40)

    screen_position = EnemySystem._screen_center(
        world_position,
        camera_offset,
    )

    assert screen_position == (140, 110)
    assert world_position == Vector2(200, 150)