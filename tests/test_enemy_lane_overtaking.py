from enemies.api import EnemySystem, Facing, _EnemyRuntime, _EnemyState
from enemies.movement import apply_lane_offset, lane_offset_for_index
from enemies.tuning import MIN_ENEMY_PATH_GAP
from shared.contracts import EnemyKind, Vector2


ROUTE = (
    Vector2(0.0, 0.0),
    Vector2(300.0, 0.0),
)


def runtime(
    identifier: str,
    progress: float,
    lane_index: int,
) -> _EnemyRuntime:
    lane_offset = lane_offset_for_index(lane_index)
    route_position = Vector2(progress, 0.0)

    return _EnemyRuntime(
        identifier=identifier,
        kind=EnemyKind.ENEMY_1,
        position=apply_lane_offset(route_position, 1.0, 0.0, lane_offset),
        route_position=route_position,
        path=ROUTE,
        path_index=1,
        health=100,
        max_health=100,
        speed=80.0,
        reward=10,
        base_damage=1,
        path_progress=progress,
        lane_index=lane_index,
        target_lane_index=lane_index,
        lane_offset=lane_offset,
        target_lane_offset=lane_offset,
        facing=Facing.RIGHT,
        last_move_direction=Facing.RIGHT,
        state=_EnemyState.WALKING,
    )


def test_fast_enemy_selects_free_lane_for_overtaking() -> None:
    system = EnemySystem()
    front = runtime("front", 50.0, 1)
    back = runtime("back", 30.0, 1)
    system._enemies = [front, back]

    allowed = system._allowed_step_distance(back, 40.0)

    assert allowed == 40.0
    assert back.target_lane_index != 1


def test_enemy_slows_down_when_all_lanes_are_blocked() -> None:
    system = EnemySystem()
    back = runtime("back", 30.0, 1)

    system._enemies = [
        runtime("front-left", 50.0, 0),
        runtime("front-center", 50.0, 1),
        runtime("front-right", 50.0, 2),
        back,
    ]

    allowed = system._allowed_step_distance(back, 40.0)

    assert allowed == max(0.0, 50.0 - 30.0 - MIN_ENEMY_PATH_GAP)
    assert back.target_lane_index == 1


def test_lane_offset_changes_visual_position() -> None:
    enemy = runtime("enemy", 60.0, 0)
    original_y = enemy.position.y

    enemy.target_lane_index = 2
    enemy.target_lane_offset = lane_offset_for_index(2)

    EnemySystem._update_lane_offset(enemy, 1.0)
    EnemySystem._refresh_visual_position(enemy)

    assert enemy.position.y != original_y
