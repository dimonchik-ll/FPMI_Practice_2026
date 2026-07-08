from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from shared.asset_manifest import ENEMY_WALK_SHEETS
from enemies.tuning import CAMPAIGN_MAX_WAVES, FINAL_BOSS_WAVE
from enemies.waves import FINAL_BOSS_KIND, is_final_boss_wave
from shared.assets import load_sprite_frame
from shared.contracts import (
    DamageCommand,
    ENEMY_DEFINITIONS,
    EnemyKind,
    EnemyView,
    GameEvent,
    GameEventKind,
    Vector2,
)


ENEMY_DISPLAY_NAMES: dict[EnemyKind, str] = {
    EnemyKind.ENEMY_1: "Гоблин-разведчик",
    EnemyKind.ENEMY_2: "Орк-громила",
    EnemyKind.ENEMY_3: "Каменный голем",
    EnemyKind.ENEMY_4: "Вождь орков",
    EnemyKind.ENEMY_5: "Мшистый кабан",
    EnemyKind.ENEMY_6: "Бронированный жук",
    EnemyKind.ENEMY_7: "Разбойник в капюшоне",
}

ENEMY_SPECIAL_TRAITS: dict[EnemyKind, str] = {
    EnemyKind.ENEMY_1: "Быстрый: скорость выше на 18%",
    EnemyKind.ENEMY_2: "Крепкая кожа: поглощает 2 урона",
    EnemyKind.ENEMY_3: "Тяжёлая броня: поглощает 6 урона",
    EnemyKind.ENEMY_4: "Ярость: ускоряется при 50% здоровья",
    EnemyKind.ENEMY_5: "Таран: крепкий враг со средней скоростью",
    EnemyKind.ENEMY_6: "Панцирь: сильно снижает входящий урон",
    EnemyKind.ENEMY_7: "Ловкач: быстрый враг с малым здоровьем",
}

WAVE_PLANS: dict[int, tuple[EnemyKind, ...]] = {
    1: (EnemyKind.ENEMY_1,) * 6,
    2: (EnemyKind.ENEMY_1,) * 8 + (EnemyKind.ENEMY_2,) * 3,
    3: (EnemyKind.ENEMY_2,) * 6 + (EnemyKind.ENEMY_3,) * 3,
    4: (EnemyKind.ENEMY_3,) * 4 + (EnemyKind.ENEMY_4,),
}


class Facing(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class _EnemyState(str, Enum):
    WALKING = "walk"
    ATTACKING = "attack"
    DYING = "death"


@dataclass(frozen=True, slots=True)
class _WaveSettings:
    spawn_interval: float
    health_multiplier: float
    speed_multiplier: float
    reward_multiplier: float


@dataclass(frozen=True, slots=True)
class _SpriteSelection:
    path: Path
    flip_horizontal: bool = False


WAVE_SETTINGS: dict[int, _WaveSettings] = {
    1: _WaveSettings(
        spawn_interval=0.85,
        health_multiplier=1.0,
        speed_multiplier=1.0,
        reward_multiplier=1.0,
    ),
    2: _WaveSettings(
        spawn_interval=0.72,
        health_multiplier=1.15,
        speed_multiplier=1.04,
        reward_multiplier=1.10,
    ),
    3: _WaveSettings(
        spawn_interval=0.60,
        health_multiplier=1.30,
        speed_multiplier=1.08,
        reward_multiplier=1.20,
    ),
    4: _WaveSettings(
        spawn_interval=0.48,
        health_multiplier=1.55,
        speed_multiplier=1.13,
        reward_multiplier=1.35,
    ),
}

ENEMY_COLORS: dict[EnemyKind, tuple[int, int, int]] = {
    EnemyKind.ENEMY_1: (93, 186, 99),
    EnemyKind.ENEMY_2: (194, 117, 61),
    EnemyKind.ENEMY_3: (113, 130, 146),
    EnemyKind.ENEMY_4: (167, 70, 90),
    EnemyKind.ENEMY_5: (118, 92, 68),
    EnemyKind.ENEMY_6: (113, 155, 55),
    EnemyKind.ENEMY_7: (113, 70, 103),
}

ANIMATION_FPS: dict[_EnemyState, int] = {
    _EnemyState.WALKING: 8,
    _EnemyState.ATTACKING: 11,
    _EnemyState.DYING: 12,
}

GOAL_ATTACK_DURATION = 0.35
DEATH_ANIMATION_DURATION = 0.55

MIN_SPAWN_INTERVAL = 0.25
MAX_ACTIVE_ENEMIES = 30
MAX_ENDLESS_SPEED_MULTIPLIER = 1.80
EPSILON = 0.0001
MIN_ENEMY_PATH_GAP = 30.0
MIN_ENEMY_SPAWN_GAP = 34.0


# FINAL_BOSS_WAVE импортируется из enemies.tuning
# FINAL_BOSS_KIND импортируется из enemies.waves


def wave_plan_for(wave_number: int) -> tuple[EnemyKind, ...]:
    if wave_number < 1:
        raise ValueError("wave_number must be positive")

    if wave_number in WAVE_PLANS:
        return WAVE_PLANS[wave_number]

    stage = wave_number - 4

    scouts = 5 + stage
    brutes = 2 + stage // 2
    golems = 1 + stage // 3
    boars = 2 + stage // 2
    beetles = 1 + stage // 3
    rogues = 2 + stage
    bosses = 1 if wave_number % 3 == 0 else 0

    return (
        (EnemyKind.ENEMY_1,) * scouts
        + (EnemyKind.ENEMY_2,) * brutes
        + (EnemyKind.ENEMY_3,) * golems
        + (EnemyKind.ENEMY_5,) * boars
        + (EnemyKind.ENEMY_6,) * beetles
        + (EnemyKind.ENEMY_7,) * rogues
        + (EnemyKind.ENEMY_4,) * bosses
    )


def wave_settings_for(wave_number: int) -> _WaveSettings:
    if wave_number < 1:
        raise ValueError("wave_number must be positive")

    if wave_number in WAVE_SETTINGS:
        return WAVE_SETTINGS[wave_number]

    stage = wave_number - 4
    base = WAVE_SETTINGS[4]

    return _WaveSettings(
        spawn_interval=max(
            MIN_SPAWN_INTERVAL,
            base.spawn_interval - stage * 0.035,
        ),
        health_multiplier=base.health_multiplier * (1 + stage * 0.14),
        speed_multiplier=min(
            MAX_ENDLESS_SPEED_MULTIPLIER,
            base.speed_multiplier * (1 + stage * 0.04),
        ),
        reward_multiplier=base.reward_multiplier * (1 + stage * 0.10),
    )


@dataclass(slots=True)
class _EnemyRuntime:
    identifier: str
    kind: EnemyKind
    position: Vector2
    path: tuple[Vector2, ...]
    path_index: int
    health: int
    max_health: int
    speed: float
    reward: int
    base_damage: int
    path_progress: float = 0.0
    facing: Facing = Facing.DOWN
    last_move_direction: Facing = Facing.DOWN
    state: _EnemyState = _EnemyState.WALKING
    animation_time: float = 0.0
    enraged: bool = False


class EnemySystem:
    def __init__(self) -> None:
        self._enemies: list[_EnemyRuntime] = []
        self._queue: list[EnemyKind] = []
        self._route: tuple[Vector2, ...] = ()
        self._spawn_cooldown = 0.0
        self._next_id = 1
        self._active_wave: int | None = None
        self._wave_settings = WAVE_SETTINGS[1]

    def start_wave(self, wave_number: int, route: tuple[Vector2, ...]) -> bool:
        if self._active_wave is not None or not route or wave_number < 1:
            return False

        self._active_wave = wave_number
        self._route = route
        self._queue = list(wave_plan_for(wave_number))
        self._wave_settings = wave_settings_for(wave_number)
        self._spawn_cooldown = 0.0

        return True

    def update(self, delta_time: float) -> list[GameEvent]:
        delta_time = max(0.0, delta_time)

        events: list[GameEvent] = []

        self._spawn_cooldown -= delta_time
        self._spawn_ready_enemies()

        survivors: list[_EnemyRuntime] = []
        ordered_enemies = sorted(
            self._enemies,
            key=lambda enemy: enemy.path_progress,
            reverse=True,
        )

        for enemy in ordered_enemies:
            enemy.animation_time += delta_time

            if enemy.state == _EnemyState.DYING:
                if enemy.animation_time < DEATH_ANIMATION_DURATION:
                    survivors.append(enemy)
                continue

            if enemy.state == _EnemyState.ATTACKING:
                if enemy.animation_time >= GOAL_ATTACK_DURATION:
                    events.append(
                        GameEvent(
                            kind=GameEventKind.ENEMY_REACHED_GOAL,
                            payload={
                                "enemy_id": enemy.identifier,
                                "damage": enemy.base_damage,
                            },
                        )
                    )
                else:
                    survivors.append(enemy)
                continue

            step_distance = self._allowed_step_distance(enemy, delta_time)

            if step_distance <= EPSILON:
                survivors.append(enemy)
                continue

            if self._move_distance(enemy, step_distance):
                enemy.state = _EnemyState.ATTACKING
                enemy.animation_time = 0.0

            survivors.append(enemy)

        self._enemies = survivors

        if self._active_wave is not None and not self._queue and not self._enemies:
            events.append(
                GameEvent(
                    kind=GameEventKind.WAVE_COMPLETED,
                    payload={"wave_number": self._active_wave},
                )
            )
            self._active_wave = None

        return events
    def apply_damage(self, commands: list[DamageCommand]) -> list[GameEvent]:
        damage_by_target: dict[str, list[int]] = {}

        for command in commands:
            if command.amount <= 0:
                continue

            damage_by_target.setdefault(command.target_id, []).append(
                command.amount
            )

        events: list[GameEvent] = []

        for enemy in self._enemies:
            if enemy.state != _EnemyState.WALKING:
                continue

            hits = damage_by_target.get(enemy.identifier)
            if not hits:
                continue

            total_damage = sum(
                self._reduce_damage(enemy.kind, amount)
                for amount in hits
            )

            enemy.health -= total_damage
            self._activate_rage(enemy)

            if enemy.health <= 0:
                enemy.health = 0
                enemy.state = _EnemyState.DYING
                enemy.animation_time = 0.0

                events.append(
                    GameEvent(
                        kind=GameEventKind.ENEMY_DEFEATED,
                        payload={
                            "enemy_id": enemy.identifier,
                            "reward": enemy.reward,
                        },
                    )
                )

        return events

    def views(self) -> tuple[EnemyView, ...]:
        return tuple(
            EnemyView(
                identifier=enemy.identifier,
                kind=enemy.kind,
                position=enemy.position,
                health=enemy.health,
                max_health=enemy.max_health,
                speed=enemy.speed,
                reward=enemy.reward,
                base_damage=enemy.base_damage,
            )
            for enemy in self._enemies
            if enemy.state == _EnemyState.WALKING
        )

    def is_wave_active(self) -> bool:
        return self._active_wave is not None

    def draw(
        self,
        surface: Any,
        camera_offset: Vector2 = Vector2(0.0, 0.0),
    ) -> None:
        import pygame

        for enemy in self._enemies:
            center = self._screen_center(enemy.position, camera_offset)
            image = self._load_animation_frame(enemy)

            if image is not None:
                if enemy.state == _EnemyState.DYING:
                    alpha = max(
                        0,
                        int(
                            255
                            * (
                                1
                                - enemy.animation_time
                                / DEATH_ANIMATION_DURATION
                            )
                        ),
                    )
                    image.set_alpha(alpha)

                surface.blit(image, image.get_rect(center=center))
            else:
                color = ENEMY_COLORS[enemy.kind]

                if enemy.state == _EnemyState.DYING:
                    color = (80, 80, 80)

                pygame.draw.circle(surface, color, center, 16)

            if enemy.state == _EnemyState.DYING:
                continue

            health_ratio = max(
                0.0,
                min(1.0, enemy.health / enemy.max_health),
            )

            health_bar = pygame.Rect(
                center[0] - 20,
                center[1] - 31,
                40,
                5,
            )

            pygame.draw.rect(surface, (63, 24, 28), health_bar)
            pygame.draw.rect(
                surface,
                (66, 180, 79),
                (
                    health_bar.x,
                    health_bar.y,
                    int(health_bar.width * health_ratio),
                    health_bar.height,
                ),
            )

    def _spawn_ready_enemies(self) -> None:
        while (
            self._queue
            and self._spawn_cooldown <= 0
            and len(self._enemies) < MAX_ACTIVE_ENEMIES
        ):
            if not self._can_spawn_at_start():
                self._spawn_cooldown = max(self._spawn_cooldown, 0.05)
                break

            self._spawn(self._queue.pop(0))
            self._spawn_cooldown += self._wave_settings.spawn_interval
    def _can_spawn_at_start(self) -> bool:
        if not self._route:
            return False

        for enemy in self._enemies:
            if enemy.state == _EnemyState.DYING:
                continue

            if enemy.path_progress < MIN_ENEMY_SPAWN_GAP:
                return False

        return True

    def _spawn(self, kind: EnemyKind) -> None:
        definition = ENEMY_DEFINITIONS[kind]
        initial_facing = self._initial_facing(self._route)

        max_health = max(
            1,
            round(
                definition.max_health
                * self._wave_settings.health_multiplier
            ),
        )

        speed = definition.speed * self._wave_settings.speed_multiplier

        if kind == EnemyKind.ENEMY_1:
            speed *= 1.18

        if kind == EnemyKind.ENEMY_7:
            speed *= 1.12

        reward = max(
            1,
            round(
                definition.reward
                * self._wave_settings.reward_multiplier
            ),
        )

        self._enemies.append(
            _EnemyRuntime(
                identifier=f"enemy-{self._next_id}",
                kind=kind,
                position=self._route[0],
                path=self._route,
                path_index=1,
                path_progress=0.0,
                health=max_health,
                max_health=max_health,
                speed=speed,
                reward=reward,
                base_damage=definition.base_damage,
                facing=initial_facing,
                last_move_direction=initial_facing,
            )
        )

        self._next_id += 1

    def _allowed_step_distance(
        self,
        enemy: _EnemyRuntime,
        delta_time: float,
    ) -> float:
        step_distance = enemy.speed * delta_time
        nearest_ahead_gap: float | None = None

        for other in self._enemies:
            if other is enemy or other.state != _EnemyState.WALKING:
                continue

            gap = other.path_progress - enemy.path_progress

            if gap <= 0:
                continue

            if nearest_ahead_gap is None or gap < nearest_ahead_gap:
                nearest_ahead_gap = gap

        if nearest_ahead_gap is None:
            return step_distance

        return min(
            step_distance,
            max(0.0, nearest_ahead_gap - MIN_ENEMY_PATH_GAP),
        )

    @staticmethod
    def _move(enemy: _EnemyRuntime, delta_time: float) -> bool:
        return EnemySystem._move_distance(enemy, enemy.speed * delta_time)

    @staticmethod
    def _move_distance(enemy: _EnemyRuntime, distance: float) -> bool:
        distance_left = max(0.0, distance)

        while distance_left > 0 and enemy.path_index < len(enemy.path):
            target = enemy.path[enemy.path_index]
            delta_x = target.x - enemy.position.x
            delta_y = target.y - enemy.position.y
            segment_distance = enemy.position.distance_to(target)

            if segment_distance <= EPSILON:
                enemy.position = target
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
                enemy.position = enemy.position.move_towards(
                    target,
                    distance_left,
                )
                enemy.path_progress += distance_left
                return False

            enemy.position = target
            enemy.path_index += 1
            enemy.path_progress += segment_distance
            distance_left -= segment_distance

        return enemy.path_index >= len(enemy.path)
    @staticmethod
    def _reduce_damage(kind: EnemyKind, amount: int) -> int:
        armor_by_kind = {
            EnemyKind.ENEMY_1: 0,
            EnemyKind.ENEMY_2: 2,
            EnemyKind.ENEMY_3: 6,
            EnemyKind.ENEMY_4: 4,
            EnemyKind.ENEMY_5: 4,
            EnemyKind.ENEMY_6: 8,
            EnemyKind.ENEMY_7: 1,
        }

        return max(1, amount - armor_by_kind[kind])

    @staticmethod
    def _activate_rage(enemy: _EnemyRuntime) -> None:
        if (
            enemy.kind == EnemyKind.ENEMY_4
            and not enemy.enraged
            and enemy.health > 0
            and enemy.health <= enemy.max_health * 0.5
        ):
            enemy.enraged = True
            enemy.speed *= 1.5

    @staticmethod
    def _initial_facing(route: tuple[Vector2, ...]) -> Facing:
        for index in range(1, len(route)):
            previous = route[index - 1]
            current = route[index]

            delta_x = current.x - previous.x
            delta_y = current.y - previous.y

            if abs(delta_x) > EPSILON or abs(delta_y) > EPSILON:
                return _facing_from_delta(
                    delta_x,
                    delta_y,
                    Facing.DOWN,
                )

        return Facing.DOWN

    @staticmethod
    def _screen_center(
        position: Vector2,
        camera_offset: Vector2,
    ) -> tuple[int, int]:
        return (
            int(round(position.x - camera_offset.x)),
            int(round(position.y - camera_offset.y)),
        )

    @staticmethod
    def _animation_selection(
        enemy: _EnemyRuntime,
    ) -> _SpriteSelection:
        walk_sheet = ENEMY_WALK_SHEETS[enemy.kind]
        seen: set[tuple[str, bool]] = set()

        for action in _actions_for_state(enemy.state):
            for filename, flip_horizontal in _directional_candidates(
                enemy.facing,
                action,
            ):
                key = (filename, flip_horizontal)

                if key in seen:
                    continue

                seen.add(key)
                candidate = walk_sheet.with_name(filename)

                if candidate.exists():
                    return _SpriteSelection(
                        path=candidate,
                        flip_horizontal=flip_horizontal,
                    )

        return _SpriteSelection(path=walk_sheet)

    @staticmethod
    def _load_animation_frame(enemy: _EnemyRuntime) -> Any | None:
        selection = EnemySystem._animation_selection(enemy)

        frame = load_sprite_frame(
            selection.path,
            frame_index=int(
                enemy.animation_time * ANIMATION_FPS[enemy.state]
            ),
            frame_size=(48, 48),
            target_size=(40, 40),
        )

        if frame is None:
            return None

        if selection.flip_horizontal:
            import pygame

            return pygame.transform.flip(frame, True, False)

        return frame


def _facing_from_delta(
    delta_x: float,
    delta_y: float,
    fallback: Facing,
) -> Facing:
    if abs(delta_x) <= EPSILON and abs(delta_y) <= EPSILON:
        return fallback

    if abs(delta_x) >= abs(delta_y):
        return Facing.RIGHT if delta_x > 0 else Facing.LEFT

    return Facing.DOWN if delta_y > 0 else Facing.UP


def _actions_for_state(state: _EnemyState) -> tuple[str, ...]:
    if state == _EnemyState.WALKING:
        return ("walk",)

    if state == _EnemyState.ATTACKING:
        return ("attack", "special", "walk")

    return ("death", "walk")


def _directional_candidates(
    facing: Facing,
    action: str,
) -> tuple[tuple[str, bool], ...]:
    if facing == Facing.RIGHT:
        return (
            (f"right_{action}.png", False),
            (f"side_{action}.png", True),
            (f"left_{action}.png", True),
            (f"down_{action}.png", False),
        )

    if facing == Facing.LEFT:
        return (
            (f"left_{action}.png", False),
            (f"side_{action}.png", False),
            (f"right_{action}.png", True),
            (f"down_{action}.png", False),
        )

    if facing == Facing.UP:
        return (
            (f"up_{action}.png", False),
            (f"side_{action}.png", False),
            (f"down_{action}.png", False),
        )

    return (
        (f"down_{action}.png", False),
        (f"side_{action}.png", False),
        (f"up_{action}.png", False),
    )