from __future__ import annotations

from typing import Any

from shared.contracts import BuildRequest, DamageCommand, EnemyView, TowerView
from towers.models import ARCHETYPES, TargetPriority, TowerRuntime, stats_for
from towers.projectiles import ProjectileSystem
from towers.sprites import TowerRenderer


class TowerSystem:
    def __init__(self) -> None:
        self._towers: list[TowerRuntime] = []
        self._projectiles = ProjectileSystem()
        self._renderer = TowerRenderer()
        self._next_id = 1

    def build(self, request: BuildRequest) -> TowerView:
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
            if tower.cooldown_remaining > 0.0:
                continue

            stats = stats_for(tower.kind, tower.level)
            target = self._find_target(tower, enemies, stats.attack_range)
            if target is None:
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
        """Удаляет башню по идентификатору и отменяет все её снаряды.

        Возвращает снимок удалённой башни. По нему интеграция может
        освободить соответствующую клетку карты и, при необходимости,
        вернуть игроку часть стоимости.
        """
        for index, tower in enumerate(self._towers):
            if tower.identifier != tower_identifier:
                continue

            removed = self._towers.pop(index)
            self._projectiles.discard_from_source(removed.identifier)
            return self._to_view(removed)
        return None

    def remove_at_cell(self, cell: tuple[int, int]) -> TowerView | None:
        """Удаляет башню, установленную на указанной клетке."""
        for tower in self._towers:
            if tower.request.cell == cell:
                return self.remove(tower.identifier)
        return None

    def remove_at_position(
        self,
        position,
        *,
        radius: float = 42.0,
    ) -> TowerView | None:
        """Удаляет ближайшую башню в радиусе клика.

        Метод удобен для обработки правой кнопки мыши. Для игрового
        состояния лучше использовать возвращаемый ``TowerView.cell``
        и освободить слот в ``CoreWorld``.
        """
        safe_radius = max(0.0, radius)
        candidates = [
            tower
            for tower in self._towers
            if tower.request.position.distance_to(position) <= safe_radius
        ]
        if not candidates:
            return None

        nearest = min(
            candidates,
            key=lambda tower: (
                tower.request.position.distance_to(position),
                tower.identifier,
            ),
        )
        return self.remove(nearest.identifier)

    def tower_at_cell(self, cell: tuple[int, int]) -> TowerView | None:
        """Возвращает башню на клетке, не изменяя игровое состояние."""
        for tower in self._towers:
            if tower.request.cell == cell:
                return self._to_view(tower)
        return None

    def upgrade(self, tower_identifier: str) -> bool:
        tower = self._tower_by_id(tower_identifier)
        if tower is None:
            return False

        max_level = ARCHETYPES[tower.kind].max_level
        if tower.level >= max_level:
            return False

        tower.level += 1
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

    def _tower_by_id(self, tower_identifier: str) -> TowerRuntime | None:
        return next(
            (tower for tower in self._towers if tower.identifier == tower_identifier),
            None,
        )

    @staticmethod
    def _to_view(tower: TowerRuntime) -> TowerView:
        return TowerView(
            identifier=tower.identifier,
            kind=tower.kind,
            position=tower.request.position,
            cell=tower.request.cell,
            cooldown_remaining=tower.cooldown_remaining,
        )
