from __future__ import annotations

import pytest

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


def build(towers: TowerSystem):
    return towers.build(BuildRequest(TowerKind.ARCHER_1, (1, 1), Vector2(0.0, 0.0)))


def build_upgraded(towers: TowerSystem, level: int):
    tower = build(towers)
    for _ in range(level - 1):
        assert towers.upgrade(tower.identifier)
    return tower


def test_only_archer_i_can_be_built_directly() -> None:
    towers = TowerSystem()

    with pytest.raises(ValueError):
        towers.build(
            BuildRequest(TowerKind.ARCHER_2, (1, 1), Vector2(0.0, 0.0))
        )


def test_upgrade_changes_tower_kind_and_exposes_next_upgrade_cost() -> None:
    towers = TowerSystem()
    tower = build(towers)

    first = towers.tower_at_cell((1, 1))
    assert first is not None
    assert first.kind == TowerKind.ARCHER_1
    assert first.level == 1
    assert first.upgrade_cost == 70

    assert towers.upgrade(tower.identifier)
    second = towers.tower_at_cell((1, 1))
    assert second is not None
    assert second.kind == TowerKind.ARCHER_2
    assert second.level == 2
    assert second.attack_type == "piercing"
    assert second.upgrade_cost == 110

    assert towers.upgrade(tower.identifier)
    third = towers.tower_at_cell((1, 1))
    assert third is not None
    assert third.kind == TowerKind.ARCHER_3
    assert third.level == 3
    assert third.attack_type == "splash"
    assert third.upgrade_cost is None


def test_tower_at_position_selects_platform_not_only_cell_center() -> None:
    towers = TowerSystem()
    tower = build(towers)

    selected = towers.tower_at_position(Vector2(0.0, -90.0))

    assert selected is not None
    assert selected.identifier == tower.identifier


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
    build_upgraded(piercing, 2)
    first = enemy("first", 80.0, 0.0)
    second = enemy("second", 110.0, 0.0)
    piercing.update(0.0, (first, second))
    first_hit = piercing.update(0.3, (first, second))
    second_hit = piercing.update(0.3, (first, second))

    assert [command.target_id for command in first_hit] == ["first", "second"]
    assert second_hit == []

    splash = TowerSystem()
    build_upgraded(splash, 3)
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


def test_default_priority_targets_first_enemy_in_input_order() -> None:
    towers = TowerSystem()
    build(towers)
    first_in_order = enemy("first-in-order", 120.0, 0.0)
    closer_second = enemy("closer-second", 30.0, 0.0)

    towers.update(0.0, (first_in_order, closer_second))
    commands = towers.update(0.3, (first_in_order, closer_second))

    assert [command.target_id for command in commands] == ["first-in-order"]


def test_chain_arrow_keeps_its_remaining_movement_after_first_hit() -> None:
    towers = TowerSystem()
    build_upgraded(towers, 2)
    first = enemy("first", 80.0, 0.0)
    second = enemy("second", 105.0, 0.0)

    towers.update(0.0, (first, second))
    commands = towers.update(0.3, (first, second))

    assert [command.target_id for command in commands] == ["first", "second"]
    assert towers.projectile_count() == 0


def test_chain_arrow_does_not_hit_the_same_enemy_twice() -> None:
    towers = TowerSystem()
    build_upgraded(towers, 2)
    first = enemy("first", 80.0, 0.0)
    second = enemy("second", 110.0, 0.0)

    towers.update(0.0, (first, second))
    commands = towers.update(0.5, (first, second))

    assert [command.target_id for command in commands] == ["first", "second"]


def test_splash_hits_enemy_inside_wide_radius() -> None:
    towers = TowerSystem()
    build_upgraded(towers, 3)
    primary = enemy("primary", 80.0, 0.0)
    inside_radius = enemy("inside-radius", 170.0, 0.0)
    outside_radius = enemy("outside-radius", 230.0, 0.0)

    towers.update(0.0, (primary, inside_radius, outside_radius))
    commands = towers.update(0.4, (primary, inside_radius, outside_radius))

    assert {command.target_id for command in commands} == {"primary", "inside-radius"}


def test_archer_turns_towards_target_before_the_next_shot() -> None:
    towers = TowerSystem()
    build(towers)
    target = enemy("target", -80.0, 20.0)

    towers.update(0.0, (target,))

    assert towers._towers[0].facing.value == "left"


def test_archer_facing_updates_while_its_attack_is_on_cooldown() -> None:
    towers = TowerSystem()
    build(towers)
    right = enemy("right", 80.0, 0.0)
    up = enemy("up", 0.0, -80.0)

    towers.update(0.0, (right,))
    assert towers._towers[0].facing.value == "right"

    towers.update(0.05, (up,))
    assert towers._towers[0].facing.value == "up"
