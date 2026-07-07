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
    """Combat parameters that supplement a level's public tower definition."""

    attack_type: AttackType
    default_priority: TargetPriority
    projectile_speed: float
    extra_pierces: int
    splash_radius: float
    splash_damage_multiplier: float


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


# Every TowerKind is exactly one upgrade level. Base damage, range and attack
# speed come from TOWER_DEFINITIONS; this table only adds attack behaviour.
# Levels II and III preserve the existing piercing and splash mechanics.
ARCHETYPES: dict[TowerKind, TowerArchetype] = {
    TowerKind.ARCHER_1: TowerArchetype(
        attack_type=AttackType.SINGLE,
        default_priority=TargetPriority.FIRST,
        projectile_speed=430.0,
        extra_pierces=0,
        splash_radius=0.0,
        splash_damage_multiplier=1.0,
    ),
    TowerKind.ARCHER_2: TowerArchetype(
        attack_type=AttackType.PIERCING,
        default_priority=TargetPriority.FIRST,
        projectile_speed=370.0,
        extra_pierces=1,
        splash_radius=0.0,
        splash_damage_multiplier=1.0,
    ),
    TowerKind.ARCHER_3: TowerArchetype(
        attack_type=AttackType.SPLASH,
        default_priority=TargetPriority.FIRST,
        projectile_speed=330.0,
        extra_pierces=0,
        splash_radius=96.0,
        splash_damage_multiplier=0.60,
    ),
    TowerKind.ARCHER_4: TowerArchetype(
        attack_type=AttackType.SPLASH,
        default_priority=TargetPriority.FIRST,
        projectile_speed=345.0,
        extra_pierces=0,
        splash_radius=112.0,
        splash_damage_multiplier=0.62,
    ),
    TowerKind.ARCHER_5: TowerArchetype(
        attack_type=AttackType.SPLASH,
        default_priority=TargetPriority.FIRST,
        projectile_speed=360.0,
        extra_pierces=0,
        splash_radius=128.0,
        splash_damage_multiplier=0.65,
    ),
    TowerKind.ARCHER_6: TowerArchetype(
        attack_type=AttackType.SPLASH,
        default_priority=TargetPriority.FIRST,
        projectile_speed=375.0,
        extra_pierces=0,
        splash_radius=144.0,
        splash_damage_multiplier=0.68,
    ),
    TowerKind.ARCHER_7: TowerArchetype(
        attack_type=AttackType.SPLASH,
        default_priority=TargetPriority.FIRST,
        projectile_speed=390.0,
        extra_pierces=0,
        splash_radius=160.0,
        splash_damage_multiplier=0.70,
    ),
    TowerKind.ARCHER_8: TowerArchetype(
        attack_type=AttackType.SPLASH,
        default_priority=TargetPriority.FIRST,
        projectile_speed=410.0,
        extra_pierces=0,
        splash_radius=180.0,
        splash_damage_multiplier=0.72,
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


def stats_for(kind: TowerKind, _level: int = 1) -> TowerStats:
    """Returns stats for a concrete tower level.

    The optional second argument stays for compatibility with earlier tower
    code. A TowerKind now fully identifies its level, so no extra multiplier
    is applied here.
    """

    archetype = ARCHETYPES[kind]
    definition = TOWER_DEFINITIONS[kind]

    return TowerStats(
        damage=definition.damage,
        attack_range=definition.attack_range,
        attacks_per_second=definition.attacks_per_second,
        projectile_speed=archetype.projectile_speed,
        attack_type=archetype.attack_type,
        extra_pierces=archetype.extra_pierces,
        splash_radius=archetype.splash_radius,
        splash_damage_multiplier=archetype.splash_damage_multiplier,
    )
