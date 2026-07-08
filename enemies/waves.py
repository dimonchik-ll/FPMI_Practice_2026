from __future__ import annotations

from dataclasses import dataclass

from shared.contracts import EnemyKind

from enemies.tuning import (
    FINAL_BOSS_WAVE,
    MAX_ENDLESS_SPEED_MULTIPLIER,
    MIN_SPAWN_INTERVAL,
)


@dataclass(frozen=True, slots=True)
class WaveSettings:
    spawn_interval: float
    health_multiplier: float
    speed_multiplier: float
    reward_multiplier: float


FINAL_BOSS_KIND = EnemyKind.ENEMY_4


CAMPAIGN_WAVE_PLANS: dict[int, tuple[EnemyKind, ...]] = {
    1: (EnemyKind.ENEMY_1,) * 6,
    2: (EnemyKind.ENEMY_1,) * 8 + (EnemyKind.ENEMY_2,) * 3,
    3: (EnemyKind.ENEMY_2,) * 6 + (EnemyKind.ENEMY_3,) * 3,
    4: (EnemyKind.ENEMY_3,) * 4 + (EnemyKind.ENEMY_4,),
}


CAMPAIGN_WAVE_SETTINGS: dict[int, WaveSettings] = {
    1: WaveSettings(
        spawn_interval=0.85,
        health_multiplier=1.0,
        speed_multiplier=1.0,
        reward_multiplier=1.0,
    ),
    2: WaveSettings(
        spawn_interval=0.72,
        health_multiplier=1.15,
        speed_multiplier=1.04,
        reward_multiplier=1.10,
    ),
    3: WaveSettings(
        spawn_interval=0.60,
        health_multiplier=1.30,
        speed_multiplier=1.08,
        reward_multiplier=1.20,
    ),
    4: WaveSettings(
        spawn_interval=0.48,
        health_multiplier=1.55,
        speed_multiplier=1.13,
        reward_multiplier=1.35,
    ),
}


def is_final_boss_wave(wave_number: int) -> bool:
    return wave_number == FINAL_BOSS_WAVE


def campaign_wave_plan(wave_number: int) -> tuple[EnemyKind, ...]:
    if wave_number < 1:
        raise ValueError("wave_number must be positive")

    if wave_number in CAMPAIGN_WAVE_PLANS:
        return CAMPAIGN_WAVE_PLANS[wave_number]

    if is_final_boss_wave(wave_number):
        return (FINAL_BOSS_KIND,)

    return endless_wave_plan(wave_number)


def endless_wave_plan(wave_number: int) -> tuple[EnemyKind, ...]:
    if wave_number < 1:
        raise ValueError("wave_number must be positive")

    stage = max(1, wave_number - 4)

    scouts = 5 + stage
    brutes = 2 + stage // 2
    golems = 1 + stage // 3
    boars = 2 + stage // 2 if hasattr(EnemyKind, "ENEMY_5") else 0
    beetles = 1 + stage // 3 if hasattr(EnemyKind, "ENEMY_6") else 0
    rogues = 2 + stage if hasattr(EnemyKind, "ENEMY_7") else 0
    bosses = 1 if wave_number % 3 == 0 else 0

    result: tuple[EnemyKind, ...] = (
        (EnemyKind.ENEMY_1,) * scouts
        + (EnemyKind.ENEMY_2,) * brutes
        + (EnemyKind.ENEMY_3,) * golems
    )

    if hasattr(EnemyKind, "ENEMY_5"):
        result += (EnemyKind.ENEMY_5,) * boars
    if hasattr(EnemyKind, "ENEMY_6"):
        result += (EnemyKind.ENEMY_6,) * beetles
    if hasattr(EnemyKind, "ENEMY_7"):
        result += (EnemyKind.ENEMY_7,) * rogues

    result += (EnemyKind.ENEMY_4,) * bosses

    return result


def campaign_wave_settings(wave_number: int) -> WaveSettings:
    if wave_number < 1:
        raise ValueError("wave_number must be positive")

    if wave_number in CAMPAIGN_WAVE_SETTINGS:
        return CAMPAIGN_WAVE_SETTINGS[wave_number]

    return endless_wave_settings(wave_number)


def endless_wave_settings(wave_number: int) -> WaveSettings:
    if wave_number < 1:
        raise ValueError("wave_number must be positive")

    stage = max(1, wave_number - 4)
    base = CAMPAIGN_WAVE_SETTINGS[4]

    return WaveSettings(
        spawn_interval=max(
            MIN_SPAWN_INTERVAL,
            base.spawn_interval - stage * 0.035,
        ),
        health_multiplier=base.health_multiplier * (1 + stage * 0.14),
        speed_multiplier=min(
            MAX_ENDLESS_SPEED_MULTIPLIER,
            base.speed_multiplier * (1 + stage * 0.04),
        ),
        reward_multiplier=base.reward_multiplier * (1 + stage * 0.10),
    )


# Совместимость со старым enemies.api.
WAVE_PLANS = CAMPAIGN_WAVE_PLANS
WAVE_SETTINGS = CAMPAIGN_WAVE_SETTINGS
wave_plan_for = campaign_wave_plan
wave_settings_for = campaign_wave_settings
_WaveSettings = WaveSettings
