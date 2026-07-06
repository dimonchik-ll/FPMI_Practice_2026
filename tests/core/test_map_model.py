from __future__ import annotations

import pytest

from core.map_model import GameMap
from shared.contracts import TileKind


@pytest.fixture()
def game_map() -> GameMap:
    return GameMap.create_default()


def test_default_map_has_expected_size(game_map: GameMap) -> None:
    assert game_map.rows == 18
    assert game_map.cols == 25
    assert game_map.tile_size == 32


def test_default_map_has_expected_pixel_size(game_map: GameMap) -> None:
    assert game_map.pixel_width == 800
    assert game_map.pixel_height == 576


def test_route_exists_and_starts_and_ends_on_road(
    game_map: GameMap,
) -> None:
    route = game_map.build_route()

    assert route

    road_centers = {
        game_map.cell_center(cell)
        for cell in game_map.road_cells
    }

    spawn_centers = {
        game_map.cell_center(cell)
        for cell in game_map.spawn_cells.intersection(
            game_map.road_cells
        )
    }

    base_centers = {
        game_map.cell_center(cell)
        for cell in game_map.base_cells.intersection(
            game_map.road_cells
        )
    }

    assert route[0] in spawn_centers
    assert route[-1] in base_centers
    assert all(point in road_centers for point in route)


def test_map_contains_seven_build_zones(
    game_map: GameMap,
) -> None:
    assert set(game_map.build_zones) == set(range(1, 8))


def test_every_build_zone_contains_four_cells(
    game_map: GameMap,
) -> None:
    for zone in game_map.build_zones.values():
        assert len(zone.cells) == 4

        for cell in zone.cells:
            assert game_map.get_build_zone(cell) == zone
            assert game_map.cell_center(cell) == zone.center


def test_any_cell_of_zone_occupies_entire_zone(
    game_map: GameMap,
) -> None:
    zone = game_map.build_zones[1]
    first_cell, second_cell, *_ = sorted(zone.cells)

    assert game_map.is_buildable(first_cell)
    assert game_map.occupy(first_cell)

    assert game_map.occupied_cells == set(zone.cells)
    assert not game_map.is_buildable(second_cell)
    assert not game_map.occupy(second_cell)


def test_release_from_any_cell_frees_entire_zone(
    game_map: GameMap,
) -> None:
    zone = game_map.build_zones[1]
    first_cell, second_cell, *_ = sorted(zone.cells)

    assert game_map.occupy(first_cell)

    game_map.release(second_cell)

    assert game_map.occupied_cells.isdisjoint(zone.cells)
    assert game_map.is_buildable(first_cell)
    assert game_map.is_buildable(second_cell)


def test_cannot_build_outside_build_zone(
    game_map: GameMap,
) -> None:
    outside_cell = next(
        (row, col)
        for row in range(game_map.rows)
        for col in range(game_map.cols)
        if game_map.get_build_zone((row, col)) is None
        and game_map.tile_at((row, col)) != TileKind.BUILD_SLOT
    )

    assert not game_map.is_buildable(outside_cell)
    assert not game_map.occupy(outside_cell)