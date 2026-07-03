from __future__ import annotations

from dataclasses import dataclass

from shared.asset_manifest import TOWER_IDLE_ASSETS
from shared.assets import load_image
from shared.contracts import (
    BuildRequest,
    DamageCommand,
    EnemyView,
    TOWER_DEFINITIONS,
    TowerKind,
    TowerView,
)


@dataclass(slots=True)
class _TowerRuntime:
    identifier: str
    request: BuildRequest
    cooldown_remaining: float = 0.0


class TowerSystem:
    def __init__(self) -> None:
        self._towers: list[_TowerRuntime] = []
        self._next_id = 1

    def build(self, request: BuildRequest) -> TowerView:
        tower = _TowerRuntime(identifier=f"tower-{self._next_id}", request=request)
        self._next_id += 1
        self._towers.append(tower)
        return self._to_view(tower)

    def update(self, delta_time: float, enemies: tuple[EnemyView, ...]) -> list[DamageCommand]:
        commands: list[DamageCommand] = []
        for tower in self._towers:
            tower.cooldown_remaining = max(0.0, tower.cooldown_remaining - delta_time)
            if tower.cooldown_remaining > 0:
                continue

            definition = TOWER_DEFINITIONS[tower.request.tower_kind]
            target = self._find_target(tower, enemies, definition.attack_range)
            if target is None:
                continue

            tower.cooldown_remaining = 1.0 / definition.attacks_per_second
            commands.append(
                DamageCommand(
                    target_id=target.identifier,
                    amount=definition.damage,
                    source_id=tower.identifier,
                )
            )
        return commands

    def views(self) -> tuple[TowerView, ...]:
        return tuple(self._to_view(tower) for tower in self._towers)

    def draw(self, surface) -> None:
        import pygame

        for tower in self._towers:
            definition = TOWER_DEFINITIONS[tower.request.tower_kind]
            image = load_image(TOWER_IDLE_ASSETS[tower.request.tower_kind], (58, 96))
            x = int(tower.request.position.x)
            y = int(tower.request.position.y)
            if image is not None:
                rect = image.get_rect(midbottom=(x, y + 24))
                surface.blit(image, rect)
            else:
                pygame.draw.circle(surface, (93, 83, 59), (x, y), 19)
                pygame.draw.circle(surface, (239, 212, 128), (x, y), 15, 2)

    def _find_target(
        self,
        tower: _TowerRuntime,
        enemies: tuple[EnemyView, ...],
        attack_range: float,
    ) -> EnemyView | None:
        valid = [
            enemy
            for enemy in enemies
            if enemy.is_alive and tower.request.position.distance_to(enemy.position) <= attack_range
        ]
        if not valid:
            return None
        return min(valid, key=lambda enemy: tower.request.position.distance_to(enemy.position))

    @staticmethod
    def _to_view(tower: _TowerRuntime) -> TowerView:
        return TowerView(
            identifier=tower.identifier,
            kind=tower.request.tower_kind,
            position=tower.request.position,
            cell=tower.request.cell,
            cooldown_remaining=tower.cooldown_remaining,
        )
