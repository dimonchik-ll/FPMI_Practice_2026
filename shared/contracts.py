from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from math import hypot
from typing import Any, TypeAlias

GridCell: TypeAlias = tuple[int, int]


class TileKind(IntEnum):
    ROAD = 0
    BUILD_SLOT = 1
    GRASS = 2
    BLOCKED = 3
    GOAL = 4
    SPAWN = 5


class TowerKind(str, Enum):
    ARCHER_1 = "archer_1"
    ARCHER_2 = "archer_2"
    ARCHER_3 = "archer_3"
    ARCHER_4 = "archer_4"
    ARCHER_5 = "archer_5"
    ARCHER_6 = "archer_6"
    ARCHER_7 = "archer_7"
    ARCHER_8 = "archer_8"


class EnemyKind(str, Enum):
    ENEMY_1 = "enemy_1"
    ENEMY_2 = "enemy_2"
    ENEMY_3 = "enemy_3"
    ENEMY_4 = "enemy_4"


class UiActionKind(str, Enum):
    SELECT_TOWER = "select_tower"
    START_WAVE = "start_wave"
    PAUSE = "pause"
    RESUME = "resume"
    RESTART = "restart"
    UPGRADE_TOWER = "upgrade_tower"
    REMOVE_TOWER = "remove_tower"
    CLOSE_TOWER_MENU = "close_tower_menu"


class GameEventKind(str, Enum):
    ENEMY_DEFEATED = "enemy_defeated"
    ENEMY_REACHED_GOAL = "enemy_reached_goal"
    WAVE_COMPLETED = "wave_completed"


@dataclass(frozen=True, slots=True)
class Vector2:
    x: float
    y: float

    def distance_to(self, other: "Vector2") -> float:
        return hypot(self.x - other.x, self.y - other.y)

    def move_towards(self, target: "Vector2", distance: float) -> "Vector2":
        total = self.distance_to(target)
        if total == 0 or distance >= total:
            return target
        ratio = distance / total
        return Vector2(
            self.x + (target.x - self.x) * ratio,
            self.y + (target.y - self.y) * ratio,
        )


@dataclass(frozen=True, slots=True)
class TowerDefinition:
    kind: TowerKind
    title: str
    cost: int
    damage: int
    attack_range: float
    attacks_per_second: float
    asset_key: str


TOWER_DEFINITIONS: dict[TowerKind, TowerDefinition] = {
    TowerKind.ARCHER_1: TowerDefinition(
        kind=TowerKind.ARCHER_1,
        title="Лучник I",
        cost=40,
        damage=12,
        attack_range=135.0,
        attacks_per_second=1.10,
        asset_key="archer_1",
    ),
    TowerKind.ARCHER_2: TowerDefinition(
        kind=TowerKind.ARCHER_2,
        title="Лучник II",
        cost=0,
        damage=22,
        attack_range=165.0,
        attacks_per_second=0.90,
        asset_key="archer_2",
    ),
    TowerKind.ARCHER_3: TowerDefinition(
        kind=TowerKind.ARCHER_3,
        title="Лучник III",
        cost=0,
        damage=34,
        attack_range=195.0,
        attacks_per_second=0.75,
        asset_key="archer_3",
    ),
    TowerKind.ARCHER_4: TowerDefinition(
        kind=TowerKind.ARCHER_4,
        title="Лучник IV",
        cost=0,
        damage=46,
        attack_range=210.0,
        attacks_per_second=0.80,
        asset_key="archer_4",
    ),
    TowerKind.ARCHER_5: TowerDefinition(
        kind=TowerKind.ARCHER_5,
        title="Лучник V",
        cost=0,
        damage=60,
        attack_range=225.0,
        attacks_per_second=0.85,
        asset_key="archer_5",
    ),
    TowerKind.ARCHER_6: TowerDefinition(
        kind=TowerKind.ARCHER_6,
        title="Лучник VI",
        cost=0,
        damage=76,
        attack_range=240.0,
        attacks_per_second=0.90,
        asset_key="archer_6",
    ),
    TowerKind.ARCHER_7: TowerDefinition(
        kind=TowerKind.ARCHER_7,
        title="Лучник VII",
        cost=0,
        damage=94,
        attack_range=260.0,
        attacks_per_second=0.95,
        asset_key="archer_7",
    ),
    TowerKind.ARCHER_8: TowerDefinition(
        kind=TowerKind.ARCHER_8,
        title="Лучник VIII",
        cost=0,
        damage=118,
        attack_range=280.0,
        attacks_per_second=1.00,
        asset_key="archer_8",
    ),
}


TOWER_LEVELS: tuple[TowerKind, ...] = (
    TowerKind.ARCHER_1,
    TowerKind.ARCHER_2,
    TowerKind.ARCHER_3,
    TowerKind.ARCHER_4,
    TowerKind.ARCHER_5,
    TowerKind.ARCHER_6,
    TowerKind.ARCHER_7,
    TowerKind.ARCHER_8,
)

TOWER_UPGRADE_PATH: dict[TowerKind, TowerKind] = dict(
    zip(TOWER_LEVELS, TOWER_LEVELS[1:])
)

# These are additional payments for the next level. The base construction cost
# comes only from TOWER_DEFINITIONS[ARCHER_1].cost.
TOWER_UPGRADE_COSTS: dict[TowerKind, int] = {
    TowerKind.ARCHER_1: 70,
    TowerKind.ARCHER_2: 110,
    TowerKind.ARCHER_3: 155,
    TowerKind.ARCHER_4: 210,
    TowerKind.ARCHER_5: 280,
    TowerKind.ARCHER_6: 365,
    TowerKind.ARCHER_7: 470,
}


def next_tower_kind(kind: TowerKind) -> TowerKind | None:
    return TOWER_UPGRADE_PATH.get(kind)


def tower_upgrade_cost(kind: TowerKind) -> int | None:
    return TOWER_UPGRADE_COSTS.get(kind)


def tower_level(kind: TowerKind) -> int:
    return TOWER_LEVELS.index(kind) + 1


def tower_max_level() -> int:
    return len(TOWER_LEVELS)


@dataclass(frozen=True, slots=True)
class EnemyDefinition:
    kind: EnemyKind
    title: str
    max_health: int
    speed: float
    reward: int
    base_damage: int
    asset_key: str


ENEMY_DEFINITIONS: dict[EnemyKind, EnemyDefinition] = {
    EnemyKind.ENEMY_1: EnemyDefinition(
        kind=EnemyKind.ENEMY_1,
        title="Враг 1",
        max_health=40,
        speed=52.0,
        reward=10,
        base_damage=1,
        asset_key="enemy_1",
    ),
    EnemyKind.ENEMY_2: EnemyDefinition(
        kind=EnemyKind.ENEMY_2,
        title="Враг 2",
        max_health=85,
        speed=42.0,
        reward=18,
        base_damage=2,
        asset_key="enemy_2",
    ),
    EnemyKind.ENEMY_3: EnemyDefinition(
        kind=EnemyKind.ENEMY_3,
        title="Враг 3",
        max_health=145,
        speed=33.0,
        reward=30,
        base_damage=3,
        asset_key="enemy_3",
    ),
    EnemyKind.ENEMY_4: EnemyDefinition(
        kind=EnemyKind.ENEMY_4,
        title="Враг 4",
        max_health=300,
        speed=25.0,
        reward=70,
        base_damage=5,
        asset_key="enemy_4",
    ),
}


@dataclass(frozen=True, slots=True)
class BuildRequest:
    tower_kind: TowerKind
    cell: GridCell
    position: Vector2


@dataclass(frozen=True, slots=True)
class DamageCommand:
    target_id: str
    amount: int
    source_id: str


@dataclass(frozen=True, slots=True)
class UiAction:
    kind: UiActionKind
    payload: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class GameEvent:
    kind: GameEventKind
    payload: dict[str, Any]


@dataclass(slots=True)
class EnemyView:
    identifier: str
    kind: EnemyKind
    position: Vector2
    health: int
    max_health: int
    speed: float
    reward: int
    base_damage: int

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    @property
    def health_ratio(self) -> float:
        if self.max_health <= 0:
            return 0.0
        return max(0.0, min(1.0, self.health / self.max_health))


@dataclass(slots=True)
class TowerView:
    identifier: str
    kind: TowerKind
    position: Vector2
    cell: GridCell
    cooldown_remaining: float
    level: int = 1
    damage: int = 0
    attack_range: float = 0.0
    attacks_per_second: float = 0.0
    attack_type: str = "single"
    upgrade_cost: int | None = None

    @property
    def can_upgrade(self) -> bool:
        return self.upgrade_cost is not None


@dataclass(frozen=True, slots=True)
class PlayerView:
    money: int
    lives: int
    score: int
    selected_tower: TowerKind | None


@dataclass(slots=True)
class PlayerState:
    money: int = 120
    lives: int = 20
    score: int = 0
    selected_tower: TowerKind | None = TowerKind.ARCHER_1

    def to_view(self) -> PlayerView:
        return PlayerView(
            money=self.money,
            lives=self.lives,
            score=self.score,
            selected_tower=self.selected_tower,
        )


@dataclass(frozen=True, slots=True)
class GameSnapshot:
    player: PlayerView
    wave_number: int
    enemies: tuple[EnemyView, ...]
    towers: tuple[TowerView, ...]
    wave_is_active: bool
    game_over: bool
    victory: bool
    paused: bool = False
