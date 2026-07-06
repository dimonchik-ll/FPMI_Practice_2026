from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from shared.asset_manifest import ENEMY_WALK_SHEETS
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
}

ENEMY_SPECIAL_TRAITS: dict[EnemyKind, str] = {
    EnemyKind.ENEMY_1: "Быстрый: скорость выше на 18%",
    EnemyKind.ENEMY_2: "Крепкая кожа: поглощает 2 урона",
    EnemyKind.ENEMY_3: "Тяжёлая броня: поглощает 6 урона",
    EnemyKind.ENEMY_4: "Ярость: ускоряется при 50% здоровья",
}

WAVE_PLANS: dict[int, tuple[EnemyKind, ...]] = {
    1: (EnemyKind.ENEMY_1,) * 6,
    2: (EnemyKind.ENEMY_1,) * 8 + (EnemyKind.ENEMY_2,) * 3,
    3: (EnemyKind.ENEMY_2,) * 6 + (EnemyKind.ENEMY_3,) * 3,
    4: (EnemyKind.ENEMY_3,) * 4 + (EnemyKind.ENEMY_4,),
}


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

ANIMATION_FILES: dict[_EnemyState, tuple[str, ...]] = {
    _EnemyState.WALKING: ("down_walk.png",),
    _EnemyState.ATTACKING: (
        "down_attack.png",
        "attack.png",
        "down_walk.png",
    ),
    _EnemyState.DYING: (
        "down_death.png",
        "death.png",
        "down_walk.png",
    ),
}

ANIMATION_FPS: dict[_EnemyState, int] = {
    _EnemyState.WALKING: 8,
    _EnemyState.ATTACKING: 11,
    _EnemyState.DYING: 12,
}

ENEMY_COLORS: dict[EnemyKind, tuple[int, int, int]] = {
    EnemyKind.ENEMY_1: (93, 186, 99),
    EnemyKind.ENEMY_2: (194, 117, 61),
    EnemyKind.ENEMY_3: (113, 130, 146),
    EnemyKind.ENEMY_4: (167, 70, 90),
}

GOAL_ATTACK_DURATION = 0.35
DEATH_ANIMATION_DURATION = 0.55


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

        fallback_wave = max(WAVE_PLANS)

        self._active_wave = wave_number
        self._route = route
        self._queue = list(
            WAVE_PLANS.get(wave_number, WAVE_PLANS[fallback_wave])
        )
        self._wave_settings = WAVE_SETTINGS.get(
            wave_number,
            WAVE_SETTINGS[max(WAVE_SETTINGS)],
        )
        self._spawn_cooldown = 0.0

        return True

    def update(self, delta_time: float) -> list[GameEvent]:
        delta_time = max(0.0, delta_time)
        events: list[GameEvent] = []

        self._spawn_cooldown -= delta_time
        self._spawn_ready_enemies()

        survivors: list[_EnemyRuntime] = []

        for enemy in self._enemies:
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

            if self._move(enemy, delta_time):
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
                self._reduce_damage(enemy.kind, hit)
                for hit in hits
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

    def draw(self, surface: Any) -> None:
        import pygame

        font = pygame.font.Font(None, 16)

        for enemy in self._enemies:
            center = (int(enemy.position.x), int(enemy.position.y))
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

            title = font.render(
                ENEMY_DISPLAY_NAMES[enemy.kind],
                True,
                (245, 245, 245),
            )
            surface.blit(
                title,
                title.get_rect(center=(center[0], center[1] - 43)),
            )

    def _spawn_ready_enemies(self) -> None:
        while self._queue and self._spawn_cooldown <= 0:
            self._spawn(self._queue.pop(0))
            self._spawn_cooldown += self._wave_settings.spawn_interval

    def _spawn(self, kind: EnemyKind) -> None:
        definition = ENEMY_DEFINITIONS[kind]

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
                health=max_health,
                max_health=max_health,
                speed=speed,
                reward=reward,
                base_damage=definition.base_damage,
            )
        )

        self._next_id += 1

    @staticmethod
    def _move(enemy: _EnemyRuntime, delta_time: float) -> bool:
        distance_left = enemy.speed * delta_time

        while distance_left > 0 and enemy.path_index < len(enemy.path):
            target = enemy.path[enemy.path_index]
            segment_distance = enemy.position.distance_to(target)

            if distance_left >= segment_distance:
                enemy.position = target
                enemy.path_index += 1
                distance_left -= segment_distance
            else:
                enemy.position = enemy.position.move_towards(
                    target,
                    distance_left,
                )
                distance_left = 0

        return enemy.path_index >= len(enemy.path)

    @staticmethod
    def _reduce_damage(kind: EnemyKind, amount: int) -> int:
        armor_by_kind = {
            EnemyKind.ENEMY_1: 0,
            EnemyKind.ENEMY_2: 2,
            EnemyKind.ENEMY_3: 6,
            EnemyKind.ENEMY_4: 4,
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
    def _sheet_for(enemy: _EnemyRuntime) -> Path:
        walk_sheet = ENEMY_WALK_SHEETS[enemy.kind]

        for file_name in ANIMATION_FILES[enemy.state]:
            candidate = walk_sheet.with_name(file_name)

            if candidate.exists():
                return candidate

        return walk_sheet

    def _load_animation_frame(self, enemy: _EnemyRuntime) -> Any | None:
        return load_sprite_frame(
            self._sheet_for(enemy),
            frame_index=int(
                enemy.animation_time * ANIMATION_FPS[enemy.state]
            ),
            frame_size=(48, 48),
            target_size=(40, 40),
        )