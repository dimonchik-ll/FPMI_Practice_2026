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
        target_position: Vector2,
        damage: int,
        speed: float,
        extra_pierces: int,
        splash_radius: float,
        splash_damage_multiplier: float,
        max_travel_distance: float,
    ) -> None:
        travel_distance = max(0.0, max_travel_distance)
        safe_speed = max(1.0, speed)
        lifetime = max(0.35, travel_distance / safe_speed + 1.0)
        self._projectiles.append(
            Projectile(
                identifier=f"projectile-{self._next_id}",
                source_id=source_id,
                target_id=target_id,
                position=position,
                damage=max(1, damage),
                speed=safe_speed,
                extra_pierces_remaining=max(0, extra_pierces),
                splash_radius=max(0.0, splash_radius),
                splash_damage_multiplier=max(0.0, splash_damage_multiplier),
                lifetime_remaining=lifetime,
                remaining_travel_distance=travel_distance,
                direction=self._direction_to(position, target_position),
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
            if projectile.lifetime_remaining <= 0.0 or projectile.remaining_travel_distance <= 0.0:
                continue

            target = enemies_by_id.get(projectile.target_id)
            if target is None:
                continue

            distance_to_target = projectile.position.distance_to(target.position)
            projectile.direction = self._direction_to(projectile.position, target.position)
            movement = min(
                projectile.speed * delta_time,
                projectile.remaining_travel_distance,
            )

            if movement < distance_to_target:
                projectile.position = projectile.position.move_towards(target.position, movement)
                projectile.remaining_travel_distance -= movement
                remaining_projectiles.append(projectile)
                continue

            projectile.position = target.position
            projectile.remaining_travel_distance -= distance_to_target
            commands.extend(
                self._create_hit_commands(
                    projectile,
                    target,
                    tuple(enemies_by_id.values()),
                )
            )
            projectile.hit_enemy_ids.add(target.identifier)

            if projectile.extra_pierces_remaining <= 0:
                continue

            projectile.extra_pierces_remaining -= 1
            next_target = self._find_next_target(
                projectile,
                tuple(enemies_by_id.values()),
            )
            if next_target is None:
                continue

            projectile.target_id = next_target.identifier
            projectile.direction = self._direction_to(
                projectile.position,
                next_target.position,
            )
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
        return Vector2(
            (target.x - source.x) / distance,
            (target.y - source.y) / distance,
        )

    @staticmethod
    def _find_next_target(
        projectile: Projectile,
        enemies: tuple[EnemyView, ...],
    ) -> EnemyView | None:
        candidates = [
            enemy
            for enemy in enemies
            if (
                enemy.identifier not in projectile.hit_enemy_ids
                and enemy.is_alive
                and projectile.position.distance_to(enemy.position)
                <= projectile.remaining_travel_distance
            )
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda enemy: (
                projectile.position.distance_to(enemy.position),
                enemy.identifier,
            ),
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

        splash_damage = max(
            1,
            round(projectile.damage * projectile.splash_damage_multiplier),
        )
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
