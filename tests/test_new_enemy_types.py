from shared.asset_manifest import ENEMY_WALK_SHEETS
from shared.contracts import ENEMY_DEFINITIONS, EnemyKind

from enemies.api import (
    ENEMY_DISPLAY_NAMES,
    FINAL_BOSS_KIND,
    FINAL_BOSS_WAVE,
    is_final_boss_wave,
    wave_plan_for,
)


NEW_ENEMIES = (
    EnemyKind.ENEMY_5,
    EnemyKind.ENEMY_6,
    EnemyKind.ENEMY_7,
)


def test_new_enemy_kinds_have_definitions() -> None:
    for kind in NEW_ENEMIES:
        assert kind in ENEMY_DEFINITIONS
        assert kind in ENEMY_DISPLAY_NAMES


def test_new_enemy_assets_exist() -> None:
    for kind in NEW_ENEMIES:
        base_path = ENEMY_WALK_SHEETS[kind]

        assert base_path.exists()
        assert base_path.with_name("up_walk.png").exists()
        assert base_path.with_name("down_walk.png").exists()
        assert base_path.with_name("left_walk.png").exists()
        assert base_path.with_name("right_walk.png").exists()


def test_new_enemies_appear_in_endless_waves() -> None:
    wave = wave_plan_for(5)

    assert EnemyKind.ENEMY_5 in wave
    assert EnemyKind.ENEMY_6 in wave
    assert EnemyKind.ENEMY_7 in wave


def test_wave_ten_still_uses_new_enemy_types() -> None:
    wave = wave_plan_for(10)

    assert EnemyKind.ENEMY_5 in wave
    assert EnemyKind.ENEMY_6 in wave
    assert EnemyKind.ENEMY_7 in wave


def test_final_boss_hook_is_prepared() -> None:
    assert FINAL_BOSS_WAVE == 11
    assert FINAL_BOSS_KIND == EnemyKind.ENEMY_4
    assert is_final_boss_wave(11)
    assert not is_final_boss_wave(10)
