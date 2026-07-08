#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path.cwd()


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")
    print(f"patched: {path}")


def find_method_bounds(lines: list[str], name: str) -> tuple[int, int]:
    def_line = None

    for index, line in enumerate(lines):
        if line.startswith(f"    def {name}("):
            def_line = index
            break

    if def_line is None:
        raise RuntimeError(f"Не найден метод {name}")

    start = def_line

    if start > 0 and lines[start - 1].startswith("    @"):
        start -= 1

    end = len(lines)

    for index in range(def_line + 1, len(lines)):
        line = lines[index]

        if line.startswith("    def ") or line.startswith("    @staticmethod"):
            end = index
            break

        if line.startswith("def ") or line.startswith("@dataclass") or line.startswith("class "):
            end = index
            break

    return start, end


def replace_method(text: str, name: str, replacement: str) -> str:
    lines = text.splitlines(keepends=True)
    start, end = find_method_bounds(lines, name)
    replacement_lines = [line + "\n" for line in replacement.rstrip("\n").splitlines()]
    lines[start:end] = replacement_lines
    return "".join(lines)


def add_name_to_tuning_import(text: str, name: str) -> str:
    marker = "from enemies.tuning import ("
    if marker in text:
        start = text.index(marker)
        end = text.index(")\n", start)
        block = text[start:end]
        if f"    {name}," in block:
            return text
        block += f"    {name},\n"
        return text[:start] + block + text[end:]

    single_prefix = "from enemies.tuning import "
    if single_prefix in text:
        line_start = text.index(single_prefix)
        line_end = text.index("\n", line_start)
        line = text[line_start:line_end]
        names = [
            item.strip()
            for item in line.removeprefix(single_prefix).split(",")
            if item.strip()
        ]
        if name not in names:
            names.append(name)

        new_line = (
            "from enemies.tuning import (\n"
            + "".join(f"    {item},\n" for item in names)
            + ")"
        )
        return text[:line_start] + new_line + text[line_end:]

    raise RuntimeError("Не найден import enemies.tuning в enemies/api.py")


def ensure_movement_import(text: str) -> str:
    if "from enemies.movement import" in text:
        return text

    import_text = (
        "from enemies.movement import (\n"
        "    apply_lane_offset,\n"
        "    lane_count,\n"
        "    lane_offset_for_index,\n"
        "    move_value_towards,\n"
        ")\n"
    )

    rendering_marker = "from enemies.rendering import ("
    if rendering_marker in text:
        start = text.index(rendering_marker)
        end = text.index(")\n", start) + 2
        return text[:end] + import_text + text[end:]

    waves_line = "from enemies.waves import"
    if waves_line in text:
        start = text.index(waves_line)
        end = text.index("\n", start) + 1
        return text[:end] + import_text + text[end:]

    raise RuntimeError("Не найдено место для импорта enemies.movement")


def patch_tuning() -> None:
    path = "enemies/tuning.py"
    text = read(path)

    if "OVERTAKE_CLEARANCE_DISTANCE" not in text:
        marker = "LANE_SWITCH_SPEED = 42.0\n"
        if marker not in text:
            raise RuntimeError("Не найден LANE_SWITCH_SPEED в enemies/tuning.py")

        text = text.replace(
            marker,
            marker
            + "OVERTAKE_CLEARANCE_DISTANCE = 28.0\n"
            + "OVERTAKE_PROGRESS_LOOKAHEAD = 72.0\n",
            1,
        )

    write(path, text)


def patch_movement() -> None:
    write(
        "enemies/movement.py",
        '''from __future__ import annotations

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
''',
    )


def patch_runtime_fields(text: str) -> str:
    lines = text.splitlines(keepends=True)

    class_start = None
    for index, line in enumerate(lines):
        if line.startswith("class _EnemyRuntime"):
            class_start = index
            break

    if class_start is None:
        raise RuntimeError("Не найден class _EnemyRuntime")

    class_end = len(lines)
    for index in range(class_start + 1, len(lines)):
        if lines[index].startswith("class ") or lines[index].startswith("def ") or lines[index].startswith("@dataclass"):
            class_end = index
            break

    block = "".join(lines[class_start:class_end])

    if "    route_position: Vector2\n" not in block:
        for index in range(class_start, class_end):
            if lines[index] == "    position: Vector2\n":
                lines.insert(index + 1, "    route_position: Vector2\n")
                class_end += 1
                break
        else:
            raise RuntimeError("Не найдено поле position в _EnemyRuntime")

    block = "".join(lines[class_start:class_end])

    if "    path_progress: float = 0.0\n" not in block:
        insert_fields = [
            "    path_progress: float = 0.0\n",
            "    lane_index: int = 0\n",
            "    target_lane_index: int = 0\n",
            "    lane_offset: float = 0.0\n",
            "    target_lane_offset: float = 0.0\n",
        ]

        for index in range(class_start, class_end):
            if lines[index] == "    base_damage: int\n":
                lines[index + 1:index + 1] = insert_fields
                break
        else:
            raise RuntimeError("Не найдено поле base_damage в _EnemyRuntime")

    return "".join(lines)


def patch_spawn(text: str) -> str:
    lines = text.splitlines(keepends=True)
    start, end = find_method_bounds(lines, "_spawn")

    method = "".join(lines[start:end])

    if "lane_index = (self._next_id - 1) % lane_count()" not in method:
        insert_index = None

        for index in range(start, end):
            if "self._enemies.append(" in lines[index]:
                insert_index = index
                break

        if insert_index is None:
            raise RuntimeError("Не найден self._enemies.append в _spawn")

        lines.insert(insert_index, "        lane_index = (self._next_id - 1) % lane_count()\n")
        lines.insert(insert_index + 1, "        lane_offset = lane_offset_for_index(lane_index)\n")
        end += 2

    method = "".join(lines[start:end])

    if "route_position=" not in method:
        for index in range(start, end):
            if "position=self._route[0]," in lines[index]:
                lines.insert(index + 1, "                route_position=self._route[0],\n")
                end += 1
                break
        else:
            raise RuntimeError("Не найден position=self._route[0] в _spawn")

    method = "".join(lines[start:end])

    if "path_progress=0.0," not in method:
        for index in range(start, end):
            if "base_damage=definition.base_damage," in lines[index]:
                insert_fields = [
                    "                path_progress=0.0,\n",
                    "                lane_index=lane_index,\n",
                    "                target_lane_index=lane_index,\n",
                    "                lane_offset=lane_offset,\n",
                    "                target_lane_offset=lane_offset,\n",
                ]
                lines[index + 1:index + 1] = insert_fields
                end += len(insert_fields)
                break
        else:
            raise RuntimeError("Не найден base_damage=definition.base_damage в _spawn")

    return "".join(lines)


def patch_update_sorting(text: str) -> str:
    lines = text.splitlines(keepends=True)
    start, end = find_method_bounds(lines, "update")
    method = "".join(lines[start:end])

    if "path_progress, reverse=True" in method:
        return text

    for index in range(start, end):
        if "for enemy in list(self._enemies):" in lines[index] or "for enemy in self._enemies:" in lines[index]:
            lines.insert(
                index,
                "        self._enemies.sort(key=lambda enemy: enemy.path_progress, reverse=True)\n",
            )
            return "".join(lines)

    return text


def patch_api() -> None:
    path = "enemies/api.py"
    text = read(path)

    text = ensure_movement_import(text)

    for name in (
        "EPSILON",
        "LANE_SWITCH_SPEED",
        "MIN_ENEMY_PATH_GAP",
        "MIN_ENEMY_SPAWN_GAP",
        "OVERTAKE_CLEARANCE_DISTANCE",
        "OVERTAKE_PROGRESS_LOOKAHEAD",
    ):
        text = add_name_to_tuning_import(text, name)

    text = text.replace("EPSILON = 0.0001\n", "")
    text = text.replace("MIN_ENEMY_PATH_GAP = 30.0\n", "")
    text = text.replace("MIN_ENEMY_SPAWN_GAP = 34.0\n", "")

    text = patch_runtime_fields(text)
    text = patch_spawn(text)
    text = patch_update_sorting(text)

    spawn_ready_method = '''    def _spawn_ready_enemies(self) -> None:
        while (
            self._queue
            and self._spawn_cooldown <= 0
            and len(self._enemies) < MAX_ACTIVE_ENEMIES
        ):
            if not self._can_spawn_at_start():
                break

            self._spawn(self._queue.pop(0))
            self._spawn_cooldown += self._wave_settings.spawn_interval'''

    move_method = '''    def _move(self, enemy: _EnemyRuntime, delta_time: float) -> bool:
        requested_distance = enemy.speed * delta_time
        allowed_distance = self._allowed_step_distance(
            enemy,
            requested_distance,
        )

        self._update_lane_offset(enemy, delta_time)

        return self._move_distance(enemy, allowed_distance)'''

    helper_methods = '''    def _allowed_step_distance(
        self,
        enemy: _EnemyRuntime,
        requested_distance: float,
    ) -> float:
        if requested_distance <= 0:
            return 0.0

        blocker = self._same_lane_blocker(enemy)

        if blocker is None:
            return requested_distance

        distance_to_blocker = blocker.path_progress - enemy.path_progress

        if distance_to_blocker > MIN_ENEMY_PATH_GAP + requested_distance:
            return requested_distance

        free_lane = self._choose_free_overtake_lane(enemy)

        if free_lane is not None:
            enemy.target_lane_index = free_lane
            enemy.target_lane_offset = lane_offset_for_index(free_lane)
            return requested_distance

        return max(0.0, distance_to_blocker - MIN_ENEMY_PATH_GAP)

    def _same_lane_blocker(
        self,
        enemy: _EnemyRuntime,
    ) -> _EnemyRuntime | None:
        best: _EnemyRuntime | None = None
        best_distance = OVERTAKE_PROGRESS_LOOKAHEAD

        for other in self._enemies:
            if other is enemy or other.state != _EnemyState.WALKING:
                continue

            if other.target_lane_index != enemy.target_lane_index:
                continue

            distance = other.path_progress - enemy.path_progress

            if 0 < distance < best_distance:
                best = other
                best_distance = distance

        return best

    def _choose_free_overtake_lane(
        self,
        enemy: _EnemyRuntime,
    ) -> int | None:
        lanes = list(range(lane_count()))
        lanes.sort(
            key=lambda lane_index: (
                lane_index == enemy.target_lane_index,
                abs(lane_index - enemy.target_lane_index),
            )
        )

        for lane_index in lanes:
            if lane_index == enemy.target_lane_index:
                continue

            if self._is_lane_clear_for(enemy, lane_index):
                return lane_index

        return None

    def _is_lane_clear_for(
        self,
        enemy: _EnemyRuntime,
        lane_index: int,
    ) -> bool:
        for other in self._enemies:
            if other is enemy or other.state != _EnemyState.WALKING:
                continue

            if other.target_lane_index != lane_index:
                continue

            if (
                abs(other.path_progress - enemy.path_progress)
                < OVERTAKE_CLEARANCE_DISTANCE
            ):
                return False

        return True

    @staticmethod
    def _update_lane_offset(
        enemy: _EnemyRuntime,
        delta_time: float,
    ) -> None:
        enemy.lane_offset = move_value_towards(
            enemy.lane_offset,
            enemy.target_lane_offset,
            LANE_SWITCH_SPEED * delta_time,
        )

        if abs(enemy.lane_offset - enemy.target_lane_offset) <= EPSILON:
            enemy.lane_offset = enemy.target_lane_offset
            enemy.lane_index = enemy.target_lane_index

    @staticmethod
    def _move_distance(
        enemy: _EnemyRuntime,
        distance: float,
    ) -> bool:
        distance_left = distance

        while distance_left > 0 and enemy.path_index < len(enemy.path):
            target = enemy.path[enemy.path_index]
            delta_x = target.x - enemy.route_position.x
            delta_y = target.y - enemy.route_position.y
            segment_distance = enemy.route_position.distance_to(target)

            if segment_distance <= EPSILON:
                enemy.route_position = target
                enemy.path_index += 1
                continue

            direction = _facing_from_delta(
                delta_x,
                delta_y,
                enemy.last_move_direction,
            )
            enemy.facing = direction
            enemy.last_move_direction = direction

            if distance_left < segment_distance:
                enemy.route_position = enemy.route_position.move_towards(
                    target,
                    distance_left,
                )
                enemy.path_progress += distance_left
                EnemySystem._refresh_visual_position(enemy)
                return False

            enemy.route_position = target
            enemy.path_index += 1
            enemy.path_progress += segment_distance
            distance_left -= segment_distance

        EnemySystem._refresh_visual_position(enemy)
        return enemy.path_index >= len(enemy.path)

    @staticmethod
    def _refresh_visual_position(enemy: _EnemyRuntime) -> None:
        delta_x, delta_y = EnemySystem._visual_direction_delta(enemy)
        enemy.position = apply_lane_offset(
            enemy.route_position,
            delta_x,
            delta_y,
            enemy.lane_offset,
        )

    @staticmethod
    def _visual_direction_delta(enemy: _EnemyRuntime) -> tuple[float, float]:
        if enemy.path_index < len(enemy.path):
            target = enemy.path[enemy.path_index]
            delta_x = target.x - enemy.route_position.x
            delta_y = target.y - enemy.route_position.y

            if abs(delta_x) > EPSILON or abs(delta_y) > EPSILON:
                return delta_x, delta_y

        if enemy.last_move_direction == Facing.RIGHT:
            return 1.0, 0.0
        if enemy.last_move_direction == Facing.LEFT:
            return -1.0, 0.0
        if enemy.last_move_direction == Facing.UP:
            return 0.0, -1.0

        return 0.0, 1.0

    def _can_spawn_at_start(self) -> bool:
        for enemy in self._enemies:
            if enemy.state != _EnemyState.WALKING:
                continue

            if enemy.path_progress < MIN_ENEMY_SPAWN_GAP:
                return False

        return True'''

    text = replace_method(text, "_spawn_ready_enemies", spawn_ready_method)
    text = replace_method(text, "_move", move_method)

    if "def _allowed_step_distance(" not in text:
        insert_before = "    @staticmethod\n    def _reduce_damage"
        if insert_before not in text:
            insert_before = "    def _reduce_damage"
        if insert_before not in text:
            raise RuntimeError("Не найдено место перед _reduce_damage")

        text = text.replace(insert_before, helper_methods + "\n\n" + insert_before, 1)

    write(path, text)


def add_tests() -> None:
    write(
        "tests/test_enemy_lane_overtaking.py",
        '''from enemies.api import EnemySystem, Facing, _EnemyRuntime, _EnemyState
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
''',
    )


def main() -> None:
    required = [
        "enemies/api.py",
        "enemies/tuning.py",
        "enemies/movement.py",
    ]

    missing = [path for path in required if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Запусти из корня проекта. Не найдены: {missing}")

    patch_tuning()
    patch_movement()
    patch_api()
    add_tests()

    print()
    print("Готово: v2 patch добавил базовую логику lane overtaking.")
    print("Проверь:")
    print("python -m pytest -q tests/test_enemy_lane_overtaking.py tests/test_enemy_health_bar_layer.py tests/test_enemy_rendering_tuning.py tests/test_new_enemy_types.py enemies/test_enemies_stage2.py tests/test_contracts.py")


if __name__ == "__main__":
    main()
