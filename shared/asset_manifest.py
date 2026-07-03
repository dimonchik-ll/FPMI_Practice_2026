from __future__ import annotations

from pathlib import Path

from shared.contracts import EnemyKind, TowerKind

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = PROJECT_ROOT / "assets"


def asset_path(*parts: str) -> Path:
    return ASSET_ROOT.joinpath(*parts)


TILE_ASSETS = {
    "grass": asset_path("tiles", "fields", "FieldsTile_39.png"),
    "road": asset_path("tiles", "fields", "FieldsTile_01.png"),
    "build_slot": asset_path("tiles", "objects", "place_for_tower_2.png"),
}

TOWER_IDLE_ASSETS = {
    TowerKind.ARCHER_1: asset_path("towers", "idle", "archer_1.png"),
    TowerKind.ARCHER_2: asset_path("towers", "idle", "archer_3.png"),
    TowerKind.ARCHER_3: asset_path("towers", "idle", "archer_5.png"),
}

TOWER_UNIT_SHEETS = {
    TowerKind.ARCHER_1: asset_path("towers", "units", "archer_1", "down_idle.png"),
    TowerKind.ARCHER_2: asset_path("towers", "units", "archer_2", "down_idle.png"),
    TowerKind.ARCHER_3: asset_path("towers", "units", "archer_3", "down_idle.png"),
}

ENEMY_WALK_SHEETS = {
    EnemyKind.ENEMY_1: asset_path("enemies", "enemy_1", "down_walk.png"),
    EnemyKind.ENEMY_2: asset_path("enemies", "enemy_2", "down_walk.png"),
    EnemyKind.ENEMY_3: asset_path("enemies", "enemy_3", "down_walk.png"),
    EnemyKind.ENEMY_4: asset_path("enemies", "enemy_4", "down_walk.png"),
}

ARROW_SHEET = asset_path("projectiles", "arrows", "arrow_1.png")
