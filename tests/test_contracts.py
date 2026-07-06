from core.map_model import GameMap
from enemies.api import EnemySystem
from shared.contracts import BuildRequest, DamageCommand, EnemyKind, GameEventKind, TowerKind, Vector2
from towers.api import TowerSystem
from ui.economy import Economy


def test_default_map_has_route() -> None:
    game_map = GameMap.create_default()
    route = game_map.build_route()
    assert len(route) > 2


def test_build_slot_can_only_be_occupied_once() -> None:
    game_map = GameMap.create_default()
    first_zone = next(iter(game_map.build_zones.values()))
    cell = next(iter(first_zone.cells))
    assert game_map.occupy(cell)
    assert not game_map.occupy(cell)


def test_tower_emits_damage_command_for_enemy_in_range() -> None:
    towers = TowerSystem()
    towers.build(BuildRequest(TowerKind.ARCHER_1, (0, 0), Vector2(100, 100)))
    from shared.contracts import EnemyView

    enemy = EnemyView("enemy-x", EnemyKind.ENEMY_1, Vector2(120, 100), 40, 40, 0, 10, 1)
    commands = towers.update(1.0, (enemy,))
    assert commands
    assert commands[0].target_id == "enemy-x"


def test_enemy_system_marks_enemy_as_defeated() -> None:
    game_map = GameMap.create_default()
    enemies = EnemySystem()
    enemies.start_wave(1, game_map.build_route())
    enemies.update(0.1)
    enemy = enemies.views()[0]
    events = enemies.apply_damage([DamageCommand(enemy.identifier, 1000, "test")])
    assert events[0].kind == GameEventKind.ENEMY_DEFEATED


def test_economy_does_not_allow_negative_purchase() -> None:
    economy = Economy()
    economy.state.money = 0
    assert not economy.buy(TowerKind.ARCHER_1)
