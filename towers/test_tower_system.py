from __future__ import annotations

from shared.contracts import BuildRequest, EnemyKind, EnemyView, TowerKind, Vector2
from towers.api import TowerSystem
from towers.models import TargetPriority


def enemy(identifier: str, x: float, y: float, *, health: int = 100, speed: float = 40.0, reward: int = 10) -> EnemyView:
    return EnemyView(
        identifier=identifier,
        kind=EnemyKind.ENEMY_1,
        position=Vector2(x, y),
        health=health,
        max_health=health,
        speed=speed,
        reward=reward,
        base_damage=1,
    )


def build(towers: TowerSystem, kind: TowerKind):
    return towers.build(BuildRequest(kind, (1, 1), Vector2(0.0, 0.0)))


def test_arrow_damage_is_emitted_only_after_projectile_reaches_enemy() -> None:
    towers = TowerSystem()
    tower = build(towers, TowerKind.ARCHER_1)
    target = enemy("target", 100.0, 0.0)

    assert towers.update(0.0, (target,)) == []
    assert towers.projectile_count() == 1

    commands = towers.update(0.5, (target,))

    assert len(commands) == 1
    assert commands[0].target_id == target.identifier
    assert commands[0].source_id == tower.identifier


def test_priority_changes_selected_target() -> None:
    towers = TowerSystem()
    tower = build(towers, TowerKind.ARCHER_1)
    weak = enemy("weak", 80.0, 0.0, health=20)
    strong = enemy("strong", 60.0, 0.0, health=200)

    assert towers.set_target_priority(tower.identifier, TargetPriority.LOWEST_HEALTH)
    towers.update(0.0, (weak, strong))
    commands = towers.update(0.5, (weak, strong))

    assert [command.target_id for command in commands] == ["weak"]


def test_piercing_arrow_can_damage_two_enemies() -> None:
    towers = TowerSystem()
    build(towers, TowerKind.ARCHER_2)
    first = enemy("first", 80.0, 0.0)
    second = enemy("second", 110.0, 0.0)

    towers.update(0.0, (first, second))
    first_hit = towers.update(0.3, (first, second))
    second_hit = towers.update(0.3, (first, second))

    assert [command.target_id for command in first_hit] == ["first"]
    assert [command.target_id for command in second_hit] == ["second"]


def test_splash_arrow_produces_damage_commands_for_nearby_enemies() -> None:
    towers = TowerSystem()
    build(towers, TowerKind.ARCHER_3)
    primary = enemy("primary", 80.0, 0.0)
    nearby = enemy("nearby", 100.0, 0.0)
    far_away = enemy("far", 170.0, 0.0)

    towers.update(0.0, (primary, nearby, far_away))
    commands = towers.update(0.4, (primary, nearby, far_away))

    command_targets = {command.target_id for command in commands}
    assert command_targets == {"primary", "nearby"}


def test_upgrade_stops_at_the_maximum_level() -> None:
    towers = TowerSystem()
    tower = build(towers, TowerKind.ARCHER_1)

    assert towers.level_of(tower.identifier) == 1
    assert towers.upgrade(tower.identifier)
    assert towers.upgrade(tower.identifier)
    assert towers.level_of(tower.identifier) == 3
    assert not towers.upgrade(tower.identifier)
