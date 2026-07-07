from core.map_model import GameMap
from enemies.api import EnemySystem
from shared.contracts import (
    BuildRequest,
    DamageCommand,
    EnemyKind,
    EnemyView,
    GameEventKind,
    TowerKind,
    Vector2,
)
from towers.api import TowerSystem
from ui.economy import Economy


def test_default_map_has_route() -> None:
    game_map = GameMap.create_default()

    route = game_map.build_route()

    assert len(route) > 2


def test_build_zone_can_only_be_occupied_once() -> None:
    game_map = GameMap.create_default()

    first_zone = next(iter(game_map.build_zones.values()))
    first_cell = next(iter(first_zone.cells))

    assert game_map.occupy(first_cell)
    assert not game_map.occupy(first_cell)


def test_tower_emits_damage_command_after_projectile_hit() -> None:
    towers = TowerSystem()

    towers.build(
        BuildRequest(
            tower_kind=TowerKind.ARCHER_1,
            cell=(0, 0),
            position=Vector2(100, 100),
        )
    )

    enemy = EnemyView(
        identifier="enemy-x",
        kind=EnemyKind.ENEMY_1,
        position=Vector2(120, 100),
        health=40,
        max_health=40,
        speed=0,
        reward=10,
        base_damage=1,
    )

    first_commands = towers.update(0.01, (enemy,))

    assert first_commands == []
    assert towers.projectile_count() == 1

    commands = towers.update(0.5, (enemy,))

    assert commands
    assert commands[0].target_id == "enemy-x"
    assert commands[0].amount > 0


def test_enemy_system_marks_enemy_as_defeated() -> None:
    game_map = GameMap.create_default()
    enemies = EnemySystem()

    assert enemies.start_wave(1, game_map.build_route())

    enemies.update(0.0)
    enemy = enemies.views()[0]

    events = enemies.apply_damage(
        [
            DamageCommand(
                target_id=enemy.identifier,
                amount=1_000,
                source_id="test",
            )
        ]
    )

    assert len(events) == 1
    assert events[0].kind == GameEventKind.ENEMY_DEFEATED
    assert events[0].payload["enemy_id"] == enemy.identifier
    assert enemies.views() == ()


def test_economy_does_not_allow_negative_purchase() -> None:
    economy = Economy()
    economy.state.money = 0

    assert not economy.buy(TowerKind.ARCHER_1)
    assert economy.state.money == 0