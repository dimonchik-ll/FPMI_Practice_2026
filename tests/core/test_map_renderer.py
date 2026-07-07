from core.map_model import GameMap
from core.map_renderer import MapRenderer


def test_build_marker_disappears_after_occupy_and_returns_after_release() -> None:
    game_map = GameMap.create_default()
    renderer = MapRenderer()

    zone_id = next(iter(game_map.build_zones))
    zone = game_map.build_zones[zone_id]
    cell = next(iter(zone.cells))

    assert renderer.build_marker_is_visible(game_map, zone_id)

    assert game_map.occupy(cell)
    assert not renderer.build_marker_is_visible(game_map, zone_id)

    game_map.release(cell)
    assert renderer.build_marker_is_visible(game_map, zone_id)
