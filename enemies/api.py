from __future__ import annotations

from dataclasses import dataclass

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

WAVE_PLANS: dict[int, tuple[EnemyKind, ...]] = {
    1: (EnemyKind.ENEMY_1,) * 5,
    2: (EnemyKind.ENEMY_1,) * 7 + (EnemyKind.ENEMY_2,) * 2,
    3: (EnemyKind.ENEMY_2,) * 5 + (EnemyKind.ENEMY_3,) * 2,
    4: (EnemyKind.ENEMY_3,) * 5 + (EnemyKind.ENEMY_4,),
}


@dataclass(slots=True)
class _EnemyRuntime:
    identifier: str
    kind: EnemyKind
    position: Vector2
    path: tuple[Vector2, ...]
    path_index: int
    health: int
    animation_time: float = 0.0


class EnemySystem:
    def __init__(self) -> None:
        self._enemies: list[_EnemyRuntime] = []
        self._queue: list[EnemyKind] = []
        self._route: tuple[Vector2, ...] = ()
        self._spawn_cooldown = 0.0
        self._next_id = 1
        self._active_wave: int | None = None

    def start_wave(self, wave_number: int, route: tuple[Vector2, ...]) -> bool:
        if self._active_wave is not None or not route:
            return False
        self._active_wave = wave_number
        self._route = route
        self._queue = list(WAVE_PLANS.get(wave_number, WAVE_PLANS[max(WAVE_PLANS)]))
        self._spawn_cooldown = 0.0
        return True

    def update(self, delta_time: float) -> list[GameEvent]:
        events: list[GameEvent] = []
        self._spawn_cooldown -= delta_time
        if self._queue and self._spawn_cooldown <= 0:
            self._spawn(self._queue.pop(0))
            self._spawn_cooldown = 0.75

        survivors: list[_EnemyRuntime] = []
        for enemy in self._enemies:
            enemy.animation_time += delta_time
            reached_goal = self._move(enemy, delta_time)
            if reached_goal:
                definition = ENEMY_DEFINITIONS[enemy.kind]
                events.append(
                    GameEvent(
                        kind=GameEventKind.ENEMY_REACHED_GOAL,
                        payload={"enemy_id": enemy.identifier, "damage": definition.base_damage},
                    )
                )
            else:
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
        damage_by_id: dict[str, int] = {}
        for command in commands:
            damage_by_id[command.target_id] = damage_by_id.get(command.target_id, 0) + command.amount

        events: list[GameEvent] = []
        survivors: list[_EnemyRuntime] = []
        for enemy in self._enemies:
            enemy.health -= damage_by_id.get(enemy.identifier, 0)
            if enemy.health <= 0:
                definition = ENEMY_DEFINITIONS[enemy.kind]
                events.append(
                    GameEvent(
                        kind=GameEventKind.ENEMY_DEFEATED,
                        payload={"enemy_id": enemy.identifier, "reward": definition.reward},
                    )
                )
            else:
                survivors.append(enemy)
        self._enemies = survivors
        return events

    def views(self) -> tuple[EnemyView, ...]:
        result: list[EnemyView] = []
        for enemy in self._enemies:
            definition = ENEMY_DEFINITIONS[enemy.kind]
            result.append(
                EnemyView(
                    identifier=enemy.identifier,
                    kind=enemy.kind,
                    position=enemy.position,
                    health=enemy.health,
                    max_health=definition.max_health,
                    speed=definition.speed,
                    reward=definition.reward,
                    base_damage=definition.base_damage,
                )
            )
        return tuple(result)

    def is_wave_active(self) -> bool:
        return self._active_wave is not None

    def draw(self, surface) -> None:
        import pygame

        for enemy in self._enemies:
            definition = ENEMY_DEFINITIONS[enemy.kind]
            frame_index = int(enemy.animation_time * 8)
            image = load_sprite_frame(
                ENEMY_WALK_SHEETS[enemy.kind],
                frame_index=frame_index,
                frame_size=(48, 48),
                target_size=(38, 38),
            )
            center = (int(enemy.position.x), int(enemy.position.y))
            if image is not None:
                surface.blit(image, image.get_rect(center=center))
            else:
                pygame.draw.circle(surface, (155, 58, 84), center, 15)

            ratio = max(0.0, min(1.0, enemy.health / definition.max_health))
            bar = pygame.Rect(center[0] - 19, center[1] - 29, 38, 5)
            pygame.draw.rect(surface, (74, 30, 34), bar)
            pygame.draw.rect(surface, (78, 175, 77), (bar.x, bar.y, int(bar.width * ratio), bar.height))

    def _spawn(self, kind: EnemyKind) -> None:
        definition = ENEMY_DEFINITIONS[kind]
        self._enemies.append(
            _EnemyRuntime(
                identifier=f"enemy-{self._next_id}",
                kind=kind,
                position=self._route[0],
                path=self._route,
                path_index=1,
                health=definition.max_health,
            )
        )
        self._next_id += 1

    @staticmethod
    def _move(enemy: _EnemyRuntime, delta_time: float) -> bool:
        definition = ENEMY_DEFINITIONS[enemy.kind]
        distance_left = definition.speed * delta_time
        while distance_left > 0 and enemy.path_index < len(enemy.path):
            target = enemy.path[enemy.path_index]
            segment_distance = enemy.position.distance_to(target)
            if distance_left >= segment_distance:
                enemy.position = target
                enemy.path_index += 1
                distance_left -= segment_distance
            else:
                enemy.position = enemy.position.move_towards(target, distance_left)
                distance_left = 0
        return enemy.path_index >= len(enemy.path)
