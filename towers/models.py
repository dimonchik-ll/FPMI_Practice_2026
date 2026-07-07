from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from shared.contracts import BuildRequest, TOWER_DEFINITIONS, TowerKind, Vector2


class AttackType(str, Enum):
    SINGLE = "single"
    PIERCING = "piercing"
    SPLASH = "splash"


class TargetPriority(str, Enum):
    FIRST = "first"
    NEAREST = "nearest"
    LOWEST_HEALTH = "lowest_health"
    HIGHEST_HEALTH = "highest_health"
    FASTEST = "fastest"
    HIGHEST_REWARD = "highest_reward"


class Facing(str, Enum):
    """One of the four sprite directions used by the archer PNG sheets."""

    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"


@dataclass(frozen=True, slots=True)
class TowerArchetype:
    attack_type: AttackType
    default_priority: TargetPriority
    projectile_speed: float
    extra_pierces_by_level: tuple[int, ...]
    splash_radius_by_level: tuple[float, ...]
    splash_damage_multiplier: float
    damage_multiplier_by_level: tuple[float, ...]
    range_multiplier_by_level: tuple[float, ...]
    attack_speed_multiplier_by_level: tuple[float, ...]

    @property
    def max_level(self) -> int:
        return len(self.damage_multiplier_by_level)


@dataclass(frozen=True, slots=True)
class TowerStats:
    damage: int
    attack_range: float
    attacks_per_second: float
    projectile_speed: float
    attack_type: AttackType
    extra_pierces: int
    splash_radius: float
    splash_damage_multiplier: float


ARCHETYPES: dict[TowerKind, TowerArchetype] = {
    TowerKind.ARCHER_1: TowerArchetype(
        attack_type=AttackType.SINGLE,
        default_priority=TargetPriority.FIRST,
        projectile_speed=430.0,
        extra_pierces_by_level=(0, 0, 0),
        splash_radius_by_level=(0.0, 0.0, 0.0),
        splash_damage_multiplier=1.0,
        damage_multiplier_by_level=(1.0, 1.35, 1.8),
        range_multiplier_by_level=(1.0, 1.08, 1.18),
        attack_speed_multiplier_by_level=(1.0, 1.2, 1.4),
    ),
    TowerKind.ARCHER_2: TowerArchetype(
        attack_type=AttackType.PIERCING,
        default_priority=TargetPriority.FIRST,
        projectile_speed=370.0,
        extra_pierces_by_level=(1, 1, 2),
        splash_radius_by_level=(0.0, 0.0, 0.0),
        splash_damage_multiplier=1.0,
        damage_multiplier_by_level=(1.0, 1.3, 1.68),
        range_multiplier_by_level=(1.0, 1.1, 1.22),
        attack_speed_multiplier_by_level=(1.0, 1.14, 1.28),
    ),
    TowerKind.ARCHER_3: TowerArchetype(
        attack_type=AttackType.SPLASH,
        default_priority=TargetPriority.FIRST,
        projectile_speed=330.0,
        extra_pierces_by_level=(0, 0, 0),
        splash_radius_by_level=(96.0, 120.0, 144.0),
        splash_damage_multiplier=0.6,
        damage_multiplier_by_level=(1.0, 1.28, 1.62),
        range_multiplier_by_level=(1.0, 1.1, 1.24),
        attack_speed_multiplier_by_level=(1.0, 1.1, 1.24),
    ),
}


@dataclass(slots=True)
class TowerRuntime:
    identifier: str
    request: BuildRequest
    level: int
    priority: TargetPriority
    cooldown_remaining: float = 0.0
    attack_animation_remaining: float = 0.0
    animation_time: float = 0.0
    facing: Facing = Facing.DOWN

    @property
    def kind(self) -> TowerKind:
        return self.request.tower_kind


@dataclass(slots=True)
class Projectile:
    identifier: str
    source_id: str
    target_id: str
    position: Vector2
    damage: int
    speed: float
    extra_pierces_remaining: int
    splash_radius: float
    splash_damage_multiplier: float
    lifetime_remaining: float
    remaining_travel_distance: float
    direction: Vector2 = Vector2(1.0, 0.0)
    hit_enemy_ids: set[str] = field(default_factory=set)


def stats_for(kind: TowerKind, level: int) -> TowerStats:
    archetype = ARCHETYPES[kind]
    definition = TOWER_DEFINITIONS[kind]
    index = max(0, min(level, archetype.max_level) - 1)

    return TowerStats(
        damage=max(1, round(definition.damage * archetype.damage_multiplier_by_level[index])),
        attack_range=definition.attack_range * archetype.range_multiplier_by_level[index],
        attacks_per_second=definition.attacks_per_second * archetype.attack_speed_multiplier_by_level[index],
        projectile_speed=archetype.projectile_speed,
        attack_type=archetype.attack_type,
        extra_pierces=archetype.extra_pierces_by_level[index],
        splash_radius=archetype.splash_radius_by_level[index],
        splash_damage_multiplier=archetype.splash_damage_multiplier,
    )
