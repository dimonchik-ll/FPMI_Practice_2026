from shared.asset_manifest import ENEMY_WALK_SHEETS
from shared.contracts import ENEMY_DEFINITIONS, EnemyKind

from enemies.api import ENEMY_DISPLAY_NAMES, wave_plan_for
from enemies.tuning import CAMPAIGN_MAX_WAVES, FINAL_BOSS_WAVE
from enemies.waves import (
    BOSS_BY_LEVEL,
    campaign_wave_plan,
    campaign_wave_settings,
    final_boss_kind_for_level,
    final_boss_wave_plan,
    is_final_boss_wave,
)


def test_final_boss_kinds_are_registered() -> None:
    assert EnemyKind.BOSS_1 in ENEMY_DEFINITIONS
    assert EnemyKind.BOSS_2 in ENEMY_DEFINITIONS
    assert EnemyKind.BOSS_1 in ENEMY_DISPLAY_NAMES
    assert EnemyKind.BOSS_2 in ENEMY_DISPLAY_NAMES


def test_final_boss_assets_exist() -> None:
    for kind in (EnemyKind.BOSS_1, EnemyKind.BOSS_2):
        base_path = ENEMY_WALK_SHEETS[kind]

        assert base_path.exists()
        assert base_path.with_name("up_walk.png").exists()
        assert base_path.with_name("down_walk.png").exists()
        assert base_path.with_name("left_walk.png").exists()
        assert base_path.with_name("right_walk.png").exists()


def test_final_boss_wave_is_after_campaign_waves() -> None:
    assert FINAL_BOSS_WAVE == CAMPAIGN_MAX_WAVES + 1
    assert is_final_boss_wave(FINAL_BOSS_WAVE)


def test_level_one_uses_first_final_boss_by_default() -> None:
    assert wave_plan_for(FINAL_BOSS_WAVE) == (EnemyKind.BOSS_1,)
    assert final_boss_wave_plan(1) == (EnemyKind.BOSS_1,)


def test_level_two_uses_second_final_boss() -> None:
    assert BOSS_BY_LEVEL[2] == EnemyKind.BOSS_2
    assert final_boss_kind_for_level(2) == EnemyKind.BOSS_2
    assert campaign_wave_plan(FINAL_BOSS_WAVE, level_number=2) == (
        EnemyKind.BOSS_2,
    )


def test_final_boss_wave_has_fixed_settings() -> None:
    settings = campaign_wave_settings(FINAL_BOSS_WAVE)

    assert settings.health_multiplier == 1.0
    assert settings.speed_multiplier == 1.0
    assert settings.reward_multiplier == 1.0
