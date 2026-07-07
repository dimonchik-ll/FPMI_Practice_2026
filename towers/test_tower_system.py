from __future__ import annotations

from shared.contracts import BuildRequest, EnemyKind, EnemyView, TowerKind, Vector2
from towers.api import TowerSystem
from towers.models import TargetPriority


def enemy(
    identifier: str,
    x: float,
    y: float,
    *,
    health: int = 100,
    speed: float = 40.0,
    reward: int = 10,
) -> EnemyView:
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


def build(towers: TowerSystem, kind: TowerKind = TowerKind.ARCHER_1):
    return towers.build(BuildRequest(kind, (1, 1), Vector2(0.0, 0.0)))


def test_projectile_uses_target_direction_immediately_after_spawn() -> None:
    towers = TowerSystem()
    build(towers)
    target = enemy("target", 0.0, -100.0)

    assert towers.update(0.0, (target,)) == []
    projectile = towers._projectiles.projectiles()[0]

    assert projectile.direction == Vector2(0.0, -1.0)


def test_damage_is_emitted_only_after_projectile_reaches_enemy() -> None:
    towers = TowerSystem()
    tower = build(towers)
    target = enemy("target", 100.0, 0.0)

    assert towers.update(0.0, (target,)) == []
    assert towers.projectile_count() == 1
    assert towers.update(0.1, (target,)) == []
    assert towers.projectile_count() == 1

    commands = towers.update(0.2, (target,))

    assert len(commands) == 1
    assert commands[0].target_id == target.identifier
    assert commands[0].source_id == tower.identifier
    assert towers.projectile_count() == 0


def test_projectile_disappears_when_its_target_is_missing_or_dead() -> None:
    towers = TowerSystem()
    build(towers)
    target = enemy("target", 100.0, 0.0)

    towers.update(0.0, (target,))
    assert towers.projectile_count() == 1

    assert towers.update(0.2, ()) == []
    assert towers.projectile_count() == 0

    towers.update(1.0, (target,))
    towers.update(0.0, (target,))
    dead_target = enemy("target", 100.0, 0.0, health=0)

    assert towers.update(0.2, (dead_target,)) == []
    assert towers.projectile_count() == 0


def test_priority_changes_selected_target() -> None:
    towers = TowerSystem()
    tower = build(towers)
    weak = enemy("weak", 80.0, 0.0, health=20)
    strong = enemy("strong", 60.0, 0.0, health=200)

    assert towers.set_target_priority(tower.identifier, TargetPriority.LOWEST_HEALTH)
    towers.update(0.0, (weak, strong))
    commands = towers.update(0.5, (weak, strong))

    assert [command.target_id for command in commands] == ["weak"]


def test_piercing_and_splash_attacks_keep_damage_commands_as_output() -> None:
    piercing = TowerSystem()
    build(piercing, TowerKind.ARCHER_2)
    first = enemy("first", 80.0, 0.0)
    second = enemy("second", 110.0, 0.0)
    piercing.update(0.0, (first, second))
    first_hit = piercing.update(0.3, (first, second))
    second_hit = piercing.update(0.3, (first, second))

    assert [command.target_id for command in first_hit] == ["first"]
    assert [command.target_id for command in second_hit] == ["second"]

    splash = TowerSystem()
    build(splash, TowerKind.ARCHER_3)
    primary = enemy("primary", 80.0, 0.0)
    nearby = enemy("nearby", 100.0, 0.0)
    splash.update(0.0, (primary, nearby))
    commands = splash.update(0.4, (primary, nearby))

    assert {command.target_id for command in commands} == {"primary", "nearby"}


def test_upgrade_increases_damage_and_stops_at_maximum_level() -> None:
    target = enemy("target", 100.0, 0.0, health=500)

    base_towers = TowerSystem()
    build(base_towers)
    base_towers.update(0.0, (target,))
    base_damage = base_towers.update(0.5, (target,))[0].amount

    towers = TowerSystem()
    tower = build(towers)
    assert towers.upgrade(tower.identifier)
    assert towers.upgrade(tower.identifier)
    assert towers.level_of(tower.identifier) == 3
    assert not towers.upgrade(tower.identifier)

    towers.update(0.0, (target,))
    upgraded_damage = towers.update(0.5, (target,))[0].amount

    assert upgraded_damage > base_damage


def test_remove_deletes_tower_and_cancels_its_projectile() -> None:
    towers = TowerSystem()
    tower = build(towers)
    target = enemy("target", 100.0, 0.0)

    towers.update(0.0, (target,))
    assert towers.projectile_count() == 1

    removed = towers.remove(tower.identifier)

    assert removed is not None
    assert removed.identifier == tower.identifier
    assert towers.views() == ()
    assert towers.projectile_count() == 0
    assert towers.update(1.0, (target,)) == []


def test_remove_at_cell_returns_removed_tower_and_rejects_missing_cell() -> None:
    towers = TowerSystem()
    first = towers.build(BuildRequest(TowerKind.ARCHER_1, (1, 1), Vector2(20.0, 20.0)))
    towers.build(BuildRequest(TowerKind.ARCHER_1, (2, 1), Vector2(80.0, 20.0)))

    assert towers.tower_at_cell((1, 1)) == first
    removed = towers.remove_at_cell((1, 1))

    assert removed == first
    assert towers.tower_at_cell((1, 1)) is None
    assert [view.identifier for view in towers.views()] == ["tower-2"]
    assert towers.remove_at_cell((1, 1)) is None


def test_remove_at_position_uses_nearest_tower_inside_radius() -> None:
    towers = TowerSystem()
    first = towers.build(BuildRequest(TowerKind.ARCHER_1, (1, 1), Vector2(20.0, 20.0)))
    second = towers.build(BuildRequest(TowerKind.ARCHER_1, (2, 1), Vector2(70.0, 20.0)))

    removed = towers.remove_at_position(Vector2(60.0, 20.0), radius=20.0)

    assert removed == second
    assert [view.identifier for view in towers.views()] == [first.identifier]
    assert towers.remove_at_position(Vector2(300.0, 300.0)) is None
