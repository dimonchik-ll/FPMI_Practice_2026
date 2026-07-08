from __future__ import annotations

from shared.contracts import DamageCommand, EnemyView, Vector2
from towers.models import Projectile


_EPSILON = 1e-6


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
        projectile_kind: str = "arrow",
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
                projectile_kind=projectile_kind,
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
        living_enemies = tuple(enemy for enemy in enemies if enemy.is_alive)
        commands: list[DamageCommand] = []
        remaining_projectiles: list[Projectile] = []

        for projectile in self._projectiles:
            projectile.lifetime_remaining -= delta_time
            if projectile.lifetime_remaining <= 0.0:
                continue

            # A projectile keeps the target selected when it was fired. It is
            # discarded when that target no longer exists, rather than jumping
            # to another arbitrary enemy.
            if projectile.target_id not in enemies_by_id:
                continue

            if self._advance_projectile(
                projectile,
                delta_time,
                enemies_by_id,
                living_enemies,
                commands,
            ):
                remaining_projectiles.append(projectile)

        self._projectiles = remaining_projectiles
        return commands

    def discard_from_source(self, source_id: str) -> int:
        """Удаляет снаряды башни, которая была продана или уничтожена."""
        before = len(self._projectiles)
        self._projectiles = [
            projectile
            for projectile in self._projectiles
            if projectile.source_id != source_id
        ]
        return before - len(self._projectiles)

    def projectiles(self) -> tuple[Projectile, ...]:
        return tuple(self._projectiles)

    def _advance_projectile(
        self,
        projectile: Projectile,
        delta_time: float,
        enemies_by_id: dict[str, EnemyView],
        living_enemies: tuple[EnemyView, ...],
        commands: list[DamageCommand],
    ) -> bool:
        """Moves one projectile through the whole frame.

        Processing every reached target inside the same frame prevents chain
        arrows from losing their remaining movement after a bounce. It also
        makes the result deterministic with both large and small frame times.
        """
        movement_budget = projectile.speed * delta_time

        while movement_budget > _EPSILON:
            if projectile.remaining_travel_distance <= _EPSILON:
                return False

            target = enemies_by_id.get(projectile.target_id)
            if target is None:
                return False

            distance_to_target = projectile.position.distance_to(target.position)
            projectile.direction = self._direction_to(projectile.position, target.position)

            # The target is out of the arrow's remaining range. The arrow can
            # still fly until that range is exhausted, but can never damage it.
            if distance_to_target > projectile.remaining_travel_distance + _EPSILON:
                movement = min(
                    movement_budget,
                    projectile.remaining_travel_distance,
                )
                projectile.position = projectile.position.move_towards(
                    target.position,
                    movement,
                )
                projectile.remaining_travel_distance -= movement
                return projectile.remaining_travel_distance > _EPSILON

            if movement_budget + _EPSILON < distance_to_target:
                projectile.position = projectile.position.move_towards(
                    target.position,
                    movement_budget,
                )
                projectile.remaining_travel_distance -= movement_budget
                return projectile.remaining_travel_distance > _EPSILON

            # The arrow reaches the current target during this frame.
            projectile.position = target.position
            projectile.remaining_travel_distance -= distance_to_target
            movement_budget = max(0.0, movement_budget - distance_to_target)
            commands.extend(
                self._create_hit_commands(
                    projectile,
                    target,
                    living_enemies,
                )
            )
            projectile.hit_enemy_ids.add(target.identifier)

            if projectile.extra_pierces_remaining <= 0:
                return False

            projectile.extra_pierces_remaining -= 1
            next_target = self._find_next_target(projectile, living_enemies)
            if next_target is None:
                return False

            projectile.target_id = next_target.identifier
            projectile.direction = self._direction_to(
                projectile.position,
                next_target.position,
            )

            # A zero-distance bounce can occur only if two different EnemyView
            # objects have the same position. The next loop still marks each
            # target once, and hit_enemy_ids guarantees termination.
            if distance_to_target <= _EPSILON and movement_budget <= _EPSILON:
                return projectile.remaining_travel_distance > _EPSILON

        return projectile.remaining_travel_distance > _EPSILON

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
                <= projectile.remaining_travel_distance + _EPSILON
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
