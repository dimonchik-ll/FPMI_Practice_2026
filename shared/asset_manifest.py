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
    "build_slot": asset_path(
        "tiles",
        "objects",
        "place_for_tower_2.png",
    ),
}


TOWER_IDLE_ASSETS = {
    TowerKind.ARCHER_1: asset_path("tiles", "towers", "idle", "archer_1.png"),
    TowerKind.ARCHER_2: asset_path("tiles", "towers", "idle", "archer_2.png"),
    TowerKind.ARCHER_3: asset_path("tiles", "towers", "idle", "archer_3.png"),
    TowerKind.ARCHER_4: asset_path("tiles", "towers", "idle", "archer_3.png"),
    TowerKind.ARCHER_5: asset_path("tiles", "towers", "idle", "archer_5.png"),
    TowerKind.ARCHER_6: asset_path("tiles", "towers", "idle", "archer_6.png"),
    TowerKind.ARCHER_7: asset_path("tiles", "towers", "idle", "archer_7.png"),
    # The code loads this file automatically if it is present in the asset pack.
    TowerKind.ARCHER_8: asset_path("tiles", "towers", "idle", "archer_8.png"),
    TowerKind.MAGE_1: asset_path("tiles", "towers", "idle", "mage_1.png"),
    TowerKind.MAGE_2: asset_path("tiles", "towers", "idle", "mage_2.png"),
    TowerKind.MAGE_3: asset_path("tiles", "towers", "idle", "mage_3.png"),
    TowerKind.MAGE_4: asset_path("tiles", "towers", "idle", "mage_4.png"),
    TowerKind.MAGE_5: asset_path("tiles", "towers", "idle", "mage_5.png"),
    TowerKind.MAGE_6: asset_path("tiles", "towers", "idle", "mage_6.png"),
    TowerKind.MAGE_7: asset_path("tiles", "towers", "idle", "mage_7.png"),
    TowerKind.MAGE_8: asset_path("tiles", "towers", "idle", "mage_8.png"),
}

# The delivered archive currently contains idle/archer_1.png … archer_7.png.
# Level VIII uses the final available model only while archer_8.png is absent.
TOWER_IDLE_FALLBACK_ASSETS = {
    TowerKind.ARCHER_8: TOWER_IDLE_ASSETS[TowerKind.ARCHER_7],
}

# There are three archer character sets. Higher architectural levels reuse the
# strongest available archer set while their base model changes every level.
TOWER_UNIT_SHEETS = {
    TowerKind.ARCHER_1: asset_path("tiles", "towers", "units", "archer_1", "down_idle.png"),
    TowerKind.ARCHER_2: asset_path("tiles", "towers", "units", "archer_1", "down_idle.png"),
    TowerKind.ARCHER_3: asset_path("tiles", "towers", "units", "archer_2", "down_idle.png"),
    TowerKind.ARCHER_4: asset_path("tiles", "towers", "units", "archer_2", "down_idle.png"),
    TowerKind.ARCHER_5: asset_path("tiles", "towers", "units", "archer_2", "down_idle.png"),
    TowerKind.ARCHER_6: asset_path("tiles", "towers", "units", "archer_3", "down_idle.png"),
    TowerKind.ARCHER_7: asset_path("tiles", "towers", "units", "archer_3", "down_idle.png"),
    TowerKind.ARCHER_8: asset_path("tiles", "towers", "units", "archer_3", "down_idle.png"),
    TowerKind.MAGE_1: asset_path("tiles", "towers", "units", "mage_1", "down_idle.png"),
    TowerKind.MAGE_2: asset_path("tiles", "towers", "units", "mage_1", "down_idle.png"),
    TowerKind.MAGE_3: asset_path("tiles", "towers", "units", "mage_1", "down_idle.png"),
    TowerKind.MAGE_4: asset_path("tiles", "towers", "units", "mage_1", "down_idle.png"),
    TowerKind.MAGE_5: asset_path("tiles", "towers", "units", "mage_1", "down_idle.png"),
    TowerKind.MAGE_6: asset_path("tiles", "towers", "units", "mage_1", "down_idle.png"),
    TowerKind.MAGE_7: asset_path("tiles", "towers", "units", "mage_1", "down_idle.png"),
    TowerKind.MAGE_8: asset_path("tiles", "towers", "units", "mage_1", "down_idle.png"),
}


ENEMY_WALK_SHEETS = {
    EnemyKind.ENEMY_1: asset_path(
        "tiles",
        "enemies",
        "enemy_1",
        "down_walk.png",
    ),
    EnemyKind.ENEMY_2: asset_path(
        "tiles",
        "enemies",
        "enemy_2",
        "down_walk.png",
    ),
    EnemyKind.ENEMY_3: asset_path(
        "tiles",
        "enemies",
        "enemy_3",
        "down_walk.png",
    ),
    EnemyKind.ENEMY_4: asset_path(
        "tiles",
        "enemies",
        "enemy_4",
        "down_walk.png",
    ),
    EnemyKind.ENEMY_5: asset_path(
        "tiles",
        "enemies",
        "enemy_5",
        "down_walk.png",
    ),
    EnemyKind.ENEMY_6: asset_path(
        "tiles",
        "enemies",
        "enemy_6",
        "down_walk.png",
    ),
    EnemyKind.ENEMY_7: asset_path(
        "tiles",
        "enemies",
        "enemy_7",
        "down_walk.png",
    ),
}

ARROW_SHEET = asset_path(
    "tiles",
    "projectiles",
    "arrows",
    "arrow_1.png",
)

FIREBALL_SHEET = asset_path(
    "tiles",
    "projectiles",
    "magic",
    "fireball.png",
)
