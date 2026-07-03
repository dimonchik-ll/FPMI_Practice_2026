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


class EnemyKind(str, Enum):
    ENEMY_1 = "enemy_1"
    ENEMY_2 = "enemy_2"
    ENEMY_3 = "enemy_3"
    ENEMY_4 = "enemy_4"


class UiActionKind(str, Enum):
    SELECT_TOWER = "select_tower"
    START_WAVE = "start_wave"


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
        attacks_per_second=1.1,
        asset_key="archer_1",
    ),
    TowerKind.ARCHER_2: TowerDefinition(
        kind=TowerKind.ARCHER_2,
        title="Лучник II",
        cost=70,
        damage=22,
        attack_range=165.0,
        attacks_per_second=0.9,
        asset_key="archer_2",
    ),
    TowerKind.ARCHER_3: TowerDefinition(
        kind=TowerKind.ARCHER_3,
        title="Лучник III",
        cost=110,
        damage=34,
        attack_range=195.0,
        attacks_per_second=0.75,
        asset_key="archer_3",
    ),
}


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
