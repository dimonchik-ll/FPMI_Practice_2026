from __future__ import annotations

from shared.contracts import DamageCommand, EnemyView, Vector2
from towers.models import Projectile


class ProjectileSystem:
    def __init__(self) -> None:
        self._projectiles: list[Projectile] = []
        self._next_id = 1

    def spawn(
        self,
        *,
        source_id: str,
        target_id: str,
        position: Vector2,
        damage: int,
        speed: float,
        extra_pierces: int,
        splash_radius: float,
        splash_damage_multiplier: float,
        max_travel_distance: float,
    ) -> None:
        lifetime = max(0.35, max_travel_distance / max(speed, 1.0) + 1.0)
        self._projectiles.append(
            Projectile(
                identifier=f"projectile-{self._next_id}",
                source_id=source_id,
                target_id=target_id,
                position=position,
                damage=damage,
                speed=speed,
                extra_pierces_remaining=extra_pierces,
                splash_radius=splash_radius,
                splash_damage_multiplier=splash_damage_multiplier,
                lifetime_remaining=lifetime,
            )
        )
        self._next_id += 1

    def update(
        self,
        delta_time: float,
        enemies: tuple[EnemyView, ...],
    ) -> list[DamageCommand]:
        delta_time = max(0.0, delta_time)
        enemies_by_id = {enemy.identifier: enemy for enemy in enemies if enemy.is_alive}
        commands: list[DamageCommand] = []
        remaining_projectiles: list[Projectile] = []

        for projectile in self._projectiles:
            projectile.lifetime_remaining -= delta_time
            if projectile.lifetime_remaining <= 0.0:
                continue

            target = enemies_by_id.get(projectile.target_id)
            if target is None:
                target = self._find_next_target(projectile, tuple(enemies_by_id.values()))
                if target is None:
                    continue
                projectile.target_id = target.identifier

            distance = projectile.position.distance_to(target.position)
            travel_distance = projectile.speed * delta_time
            projectile.direction = self._direction_to(projectile.position, target.position)
            projectile.position = projectile.position.move_towards(target.position, travel_distance)

            if travel_distance < distance:
                remaining_projectiles.append(projectile)
                continue

            commands.extend(self._create_hit_commands(projectile, target, tuple(enemies_by_id.values())))
            projectile.hit_enemy_ids.add(target.identifier)

            if projectile.extra_pierces_remaining <= 0:
                continue

            projectile.extra_pierces_remaining -= 1
            next_target = self._find_next_target(projectile, tuple(enemies_by_id.values()))
            if next_target is None:
                continue

            projectile.target_id = next_target.identifier
            remaining_projectiles.append(projectile)

        self._projectiles = remaining_projectiles
        return commands

    def projectiles(self) -> tuple[Projectile, ...]:
        return tuple(self._projectiles)

    @staticmethod
    def _direction_to(source: Vector2, target: Vector2) -> Vector2:
        distance = source.distance_to(target)
        if distance == 0.0:
            return Vector2(1.0, 0.0)
        return Vector2((target.x - source.x) / distance, (target.y - source.y) / distance)

    @staticmethod
    def _find_next_target(projectile: Projectile, enemies: tuple[EnemyView, ...]) -> EnemyView | None:
        candidates = [
            enemy
            for enemy in enemies
            if enemy.identifier not in projectile.hit_enemy_ids and enemy.is_alive
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda enemy: (projectile.position.distance_to(enemy.position), enemy.identifier),
        )

    @staticmethod
    def _create_hit_commands(
        projectile: Projectile,
        target: EnemyView,
        enemies: tuple[EnemyView, ...],
    ) -> list[DamageCommand]:
        commands = [
            DamageCommand(
                target_id=target.identifier,
                amount=projectile.damage,
                source_id=projectile.source_id,
            )
        ]

        if projectile.splash_radius <= 0.0:
            return commands

        splash_damage = max(1, round(projectile.damage * projectile.splash_damage_multiplier))
        for enemy in enemies:
            if enemy.identifier == target.identifier or not enemy.is_alive:
                continue
            if enemy.position.distance_to(target.position) > projectile.splash_radius:
                continue
            commands.append(
                DamageCommand(
                    target_id=enemy.identifier,
                    amount=splash_damage,
                    source_id=projectile.source_id,
                )
            )
        return commands
