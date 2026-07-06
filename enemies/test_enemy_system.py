from enemies.api import (
    ENEMY_DISPLAY_NAMES,
    MIN_SPAWN_INTERVAL,
    EnemySystem,
    WAVE_PLANS,
    wave_plan_for,
    wave_settings_for,
)
from shared.contracts import DamageCommand, EnemyKind, GameEventKind, Vector2


LONG_ROUTE = (
    Vector2(0, 0),
    Vector2(10_000, 0),
)

SHORT_ROUTE = (
    Vector2(0, 0),
    Vector2(1, 0),
)


def test_every_enemy_has_display_name() -> None:
    assert set(ENEMY_DISPLAY_NAMES) == set(EnemyKind)


def test_cannot_start_wave_without_route() -> None:
    enemies = EnemySystem()

    assert not enemies.start_wave(1, ())
    assert not enemies.is_wave_active()


def test_cannot_start_second_wave_while_first_is_active() -> None:
    enemies = EnemySystem()

    assert enemies.start_wave(1, LONG_ROUTE)
    assert not enemies.start_wave(2, LONG_ROUTE)


def test_enemy_moves_along_route() -> None:
    enemies = EnemySystem()
    enemies.start_wave(1, LONG_ROUTE)

    enemies.update(0.0)
    before = enemies.views()[0]

    enemies.update(0.5)
    after = enemies.views()[0]

    assert after.position.x > before.position.x
    assert after.position.y == before.position.y


def test_enemy_defeat_creates_event_and_hides_enemy() -> None:
    enemies = EnemySystem()
    enemies.start_wave(1, LONG_ROUTE)
    enemies.update(0.0)

    enemy = enemies.views()[0]

    events = enemies.apply_damage(
        [
            DamageCommand(
                target_id=enemy.identifier,
                amount=10_000,
                source_id="test",
            )
        ]
    )

    assert events[0].kind == GameEventKind.ENEMY_DEFEATED
    assert events[0].payload["enemy_id"] == enemy.identifier
    assert enemies.views() == ()


def test_enemy_reaching_goal_completes_wave(monkeypatch) -> None:
    monkeypatch.setitem(WAVE_PLANS, 99, (EnemyKind.ENEMY_1,))

    enemies = EnemySystem()
    assert enemies.start_wave(99, SHORT_ROUTE)

    enemies.update(0.0)
    enemies.update(0.1)
    events = enemies.update(0.4)

    event_kinds = {event.kind for event in events}

    assert GameEventKind.ENEMY_REACHED_GOAL in event_kinds
    assert GameEventKind.WAVE_COMPLETED in event_kinds
    assert not enemies.is_wave_active()


def test_orc_reduces_small_damage(monkeypatch) -> None:
    monkeypatch.setitem(WAVE_PLANS, 98, (EnemyKind.ENEMY_2,))

    enemies = EnemySystem()
    enemies.start_wave(98, LONG_ROUTE)
    enemies.update(0.0)

    before = enemies.views()[0]

    enemies.apply_damage(
        [
            DamageCommand(
                target_id=before.identifier,
                amount=2,
                source_id="test",
            )
        ]
    )

    after = enemies.views()[0]

    assert after.health == before.health - 1


def test_boss_enters_rage_below_half_health(monkeypatch) -> None:
    monkeypatch.setitem(WAVE_PLANS, 97, (EnemyKind.ENEMY_4,))

    enemies = EnemySystem()
    enemies.start_wave(97, LONG_ROUTE)
    enemies.update(0.0)

    before = enemies.views()[0]

    enemies.apply_damage(
        [
            DamageCommand(
                target_id=before.identifier,
                amount=before.max_health // 2 + 6,
                source_id="test",
            )
        ]
    )

    after = enemies.views()[0]

    assert after.health <= after.max_health / 2
    assert after.speed > before.speed


def test_wave_five_has_more_enemies_than_wave_four() -> None:
    assert len(wave_plan_for(5)) > len(wave_plan_for(4))


def test_dynamic_wave_has_boss_every_third_wave() -> None:
    assert EnemyKind.ENEMY_4 in wave_plan_for(6)
    assert EnemyKind.ENEMY_4 in wave_plan_for(9)


def test_later_waves_are_stronger_and_spawn_faster() -> None:
    wave_four = wave_settings_for(4)
    wave_five = wave_settings_for(5)

    assert wave_five.health_multiplier > wave_four.health_multiplier
    assert wave_five.speed_multiplier > wave_four.speed_multiplier
    assert wave_five.spawn_interval < wave_four.spawn_interval


def test_spawn_interval_has_lower_limit() -> None:
    assert wave_settings_for(1_000).spawn_interval == MIN_SPAWN_INTERVAL