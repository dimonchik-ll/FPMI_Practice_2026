from __future__ import annotations

from dataclasses import dataclass

from shared.contracts import Vector2

from enemies.tuning import EPSILON, LANE_OFFSETS


@dataclass(frozen=True, slots=True)
class MovementStep:
    position: Vector2
    reached_end: bool
    distance_passed: float


def route_initial_direction(route: tuple[Vector2, ...]) -> tuple[float, float]:
    for index in range(1, len(route)):
        previous = route[index - 1]
        current = route[index]
        delta_x = current.x - previous.x
        delta_y = current.y - previous.y

        if abs(delta_x) > EPSILON or abs(delta_y) > EPSILON:
            return delta_x, delta_y

    return 0.0, 1.0


def lane_count() -> int:
    return len(LANE_OFFSETS)


def clamp_lane_index(index: int) -> int:
    return max(0, min(lane_count() - 1, index))


def lane_offset_for_index(index: int) -> float:
    return LANE_OFFSETS[clamp_lane_index(index)]


def move_value_towards(current: float, target: float, step: float) -> float:
    if abs(target - current) <= step:
        return target

    if target > current:
        return current + step

    return current - step


def apply_lane_offset(
    position: Vector2,
    direction_x: float,
    direction_y: float,
    lane_offset: float,
) -> Vector2:
    length = (direction_x * direction_x + direction_y * direction_y) ** 0.5

    if length <= EPSILON:
        return position

    normal_x = -direction_y / length
    normal_y = direction_x / length

    return Vector2(
        position.x + normal_x * lane_offset,
        position.y + normal_y * lane_offset,
    )
