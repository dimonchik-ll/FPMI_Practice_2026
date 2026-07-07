from __future__ import annotations

from dataclasses import replace
from typing import Any

from shared.contracts import (
    BuildRequest,
    DamageCommand,
    EnemyView,
    TowerKind,
    TowerView,
    next_tower_kind,
    tower_level,
    tower_upgrade_cost,
)
from towers.models import ARCHETYPES, Facing, TargetPriority, TowerRuntime, stats_for
from towers.projectiles import ProjectileSystem
from towers.sprites import TowerRenderer


_INITIAL_BUILD_KIND = TowerKind.ARCHER_1
_TOWER_CLICK_HALF_WIDTH = 52.0
_TOWER_CLICK_TOP_OFFSET = 118.0
_TOWER_CLICK_BOTTOM_OFFSET = 42.0


class TowerSystem:
    def __init__(self) -> None:
        self._towers: list[TowerRuntime] = []
        self._projectiles = ProjectileSystem()
        self._renderer = TowerRenderer()
        self._next_id = 1

    def build(self, request: BuildRequest) -> TowerView:
        """Builds only the initial archer level.

        Levels II–VIII are upgrades of an existing tower. Keeping the guard
        here prevents bypassing the UI by creating a high-level tower directly
        from integration code.
        """
        if request.tower_kind != _INITIAL_BUILD_KIND:
            raise ValueError(
                "Можно построить только Лучника I. "
                "Лучники II–VIII получаются через улучшение."
            )

        archetype = ARCHETYPES[request.tower_kind]
        tower = TowerRuntime(
            identifier=f"tower-{self._next_id}",
            request=request,
            level=1,
            priority=archetype.default_priority,
        )
        self._next_id += 1
        self._towers.append(tower)
        return self._to_view(tower)

    def update(
        self,
        delta_time: float,
        enemies: tuple[EnemyView, ...],
    ) -> list[DamageCommand]:
        delta_time = max(0.0, delta_time)
        damage_commands = self._projectiles.update(delta_time, enemies)

        for tower in self._towers:
            tower.animation_time += delta_time
            tower.attack_animation_remaining = max(
                0.0,
                tower.attack_animation_remaining - delta_time,
            )
            tower.cooldown_remaining = max(0.0, tower.cooldown_remaining - delta_time)

            # The current TowerKind already represents the current upgrade
            # level, so there is no second multiplier based on tower.level.
            stats = stats_for(tower.kind, 1)
            target = self._find_target(tower, enemies, stats.attack_range)
            if target is not None:
                tower.facing = self._facing_towards(tower, target)

            if tower.cooldown_remaining > 0.0 or target is None:
                continue

            tower.cooldown_remaining = 1.0 / stats.attacks_per_second
            tower.attack_animation_remaining = 0.22
            self._projectiles.spawn(
                source_id=tower.identifier,
                target_id=target.identifier,
                position=tower.request.position,
                target_position=target.position,
                damage=stats.damage,
                speed=stats.projectile_speed,
                extra_pierces=stats.extra_pierces,
                splash_radius=stats.splash_radius,
                splash_damage_multiplier=stats.splash_damage_multiplier,
                max_travel_distance=stats.attack_range,
            )

        return damage_commands

    def remove(self, tower_identifier: str) -> TowerView | None:
        """Removes a tower by identifier and cancels its flying projectiles."""
        for index, tower in enumerate(self._towers):
            if tower.identifier != tower_identifier:
                continue

            removed = self._towers.pop(index)
            self._projectiles.discard_from_source(removed.identifier)
            return self._to_view(removed)
        return None

    def remove_at_cell(self, cell: tuple[int, int]) -> TowerView | None:
        """Removes the tower installed on the specified build cell."""
        tower = next(
            (candidate for candidate in self._towers if candidate.request.cell == cell),
            None,
        )
        return None if tower is None else self.remove(tower.identifier)

    def remove_at_position(
        self,
        position,
        *,
        radius: float | None = None,
    ) -> TowerView | None:
        """Compatibility helper for callers that intentionally remove by click."""
        tower = self._tower_at_position_runtime(position, radius=radius)
        return None if tower is None else self.remove(tower.identifier)

    def tower_at_cell(self, cell: tuple[int, int]) -> TowerView | None:
        """Returns a tower on a build cell without changing game state."""
        tower = next(
            (candidate for candidate in self._towers if candidate.request.cell == cell),
            None,
        )
        return None if tower is None else self._to_view(tower)

    def tower_at_position(
        self,
        position,
        *,
        radius: float | None = None,
    ) -> TowerView | None:
        """Returns the visible tower under a map click without deleting it.

        The selection hitbox covers the whole tower sprite, including the top
        platform, rather than only the centre of its build cell.
        """
        tower = self._tower_at_position_runtime(position, radius=radius)
        return None if tower is None else self._to_view(tower)

    def can_upgrade(self, tower_identifier: str) -> bool:
        tower = self._tower_by_id(tower_identifier)
        return tower is not None and next_tower_kind(tower.kind) is not None

    def upgrade_cost(self, tower_identifier: str) -> int | None:
        tower = self._tower_by_id(tower_identifier)
        if tower is None:
            return None
        return tower_upgrade_cost(tower.kind)

    def upgrade(self, tower_identifier: str) -> bool:
        """Upgrades a tower by one step from Archer I to Archer VIII.

        The tower keeps its identifier and build cell, while its asset, attack
        type and base statistics switch to the next TowerKind.
        """
        tower = self._tower_by_id(tower_identifier)
        if tower is None:
            return False

        upgraded_kind = next_tower_kind(tower.kind)
        if upgraded_kind is None:
            return False

        tower.request = replace(tower.request, tower_kind=upgraded_kind)
        tower.level = tower_level(upgraded_kind)
        tower.cooldown_remaining = 0.0
        tower.attack_animation_remaining = 0.0
        return True

    def level_of(self, tower_identifier: str) -> int | None:
        tower = self._tower_by_id(tower_identifier)
        return None if tower is None else tower.level

    def set_target_priority(
        self,
        tower_identifier: str,
        priority: TargetPriority | str,
    ) -> bool:
        tower = self._tower_by_id(tower_identifier)
        if tower is None:
            return False

        try:
            tower.priority = (
                priority if isinstance(priority, TargetPriority) else TargetPriority(priority)
            )
        except (TypeError, ValueError):
            return False
        return True

    def target_priority_of(self, tower_identifier: str) -> TargetPriority | None:
        tower = self._tower_by_id(tower_identifier)
        return None if tower is None else tower.priority

    def views(self) -> tuple[TowerView, ...]:
        return tuple(self._to_view(tower) for tower in self._towers)

    def projectile_count(self) -> int:
        return len(self._projectiles.projectiles())

    def draw(self, surface: Any) -> None:
        for tower in self._towers:
            self._renderer.draw_tower(surface, tower)
        for projectile in self._projectiles.projectiles():
            self._renderer.draw_projectile(surface, projectile)

    def _tower_at_position_runtime(self, position, *, radius: float | None) -> TowerRuntime | None:
        if radius is not None:
            safe_radius = max(0.0, radius)
            candidates = [
                tower
                for tower in self._towers
                if tower.request.position.distance_to(position) <= safe_radius
            ]
        else:
            candidates = [
                tower
                for tower in self._towers
                if self._contains_visible_tower(tower, position)
            ]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda tower: (
                tower.request.position.distance_to(position),
                tower.identifier,
            ),
        )

    @staticmethod
    def _contains_visible_tower(tower: TowerRuntime, position) -> bool:
        origin = tower.request.position
        return (
            origin.x - _TOWER_CLICK_HALF_WIDTH <= position.x <= origin.x + _TOWER_CLICK_HALF_WIDTH
            and origin.y - _TOWER_CLICK_TOP_OFFSET <= position.y <= origin.y + _TOWER_CLICK_BOTTOM_OFFSET
        )

    @staticmethod
    def _find_target(
        tower: TowerRuntime,
        enemies: tuple[EnemyView, ...],
        attack_range: float,
    ) -> EnemyView | None:
        valid = [
            enemy
            for enemy in enemies
            if (
                enemy.is_alive
                and tower.request.position.distance_to(enemy.position) <= attack_range
            )
        ]
        if not valid:
            return None

        # EnemySystem provides enemies in their route order. The default
        # priority uses the first valid item exactly as it appears in that tuple.
        if tower.priority == TargetPriority.FIRST:
            return valid[0]

        def key(enemy: EnemyView) -> tuple[float, float, str]:
            distance = tower.request.position.distance_to(enemy.position)
            if tower.priority == TargetPriority.LOWEST_HEALTH:
                return float(enemy.health), distance, enemy.identifier
            if tower.priority == TargetPriority.HIGHEST_HEALTH:
                return -float(enemy.health), distance, enemy.identifier
            if tower.priority == TargetPriority.FASTEST:
                return -float(enemy.speed), distance, enemy.identifier
            if tower.priority == TargetPriority.HIGHEST_REWARD:
                return -float(enemy.reward), distance, enemy.identifier
            return distance, enemy.health_ratio, enemy.identifier

        return min(valid, key=key)

    @staticmethod
    def _facing_towards(tower: TowerRuntime, target: EnemyView) -> Facing:
        dx = target.position.x - tower.request.position.x
        dy = target.position.y - tower.request.position.y
        if abs(dx) >= abs(dy):
            return Facing.RIGHT if dx >= 0.0 else Facing.LEFT
        return Facing.DOWN if dy >= 0.0 else Facing.UP

    def _tower_by_id(self, tower_identifier: str) -> TowerRuntime | None:
        return next(
            (tower for tower in self._towers if tower.identifier == tower_identifier),
            None,
        )

    @staticmethod
    def _to_view(tower: TowerRuntime) -> TowerView:
        stats = stats_for(tower.kind, 1)
        return TowerView(
            identifier=tower.identifier,
            kind=tower.kind,
            position=tower.request.position,
            cell=tower.request.cell,
            cooldown_remaining=tower.cooldown_remaining,
            level=tower.level,
            damage=stats.damage,
            attack_range=stats.attack_range,
            attacks_per_second=stats.attacks_per_second,
            attack_type=stats.attack_type.value,
            upgrade_cost=tower_upgrade_cost(tower.kind),
        )
