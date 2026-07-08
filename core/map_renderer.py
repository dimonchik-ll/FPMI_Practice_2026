from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame
from pytmx import TiledTileLayer
from pytmx.util_pygame import load_pygame

from core.map_model import GameMap
from shared.contracts import TileKind


class MapRenderer:
    DRAW_LAYERS = {
        "Ground",
        "Road",
        "Shadow",
        "Stone",
        "Bush",
        "Tree",
        "Camp",
        "Decor",
        "Dirt",
    }

    BUILDABLE_LAYER = "Buildable"

    def __init__(self) -> None:
        self._tmx_data: Any | None = None
        self._loaded_path: Path | None = None

    def draw(
        self,
        surface: pygame.Surface,
        game_map: GameMap,
    ) -> None:
        if game_map.tmx_path is None:
            self._draw_fallback(surface, game_map)
            return

        tmx_data = self._load_tmx(game_map)

        for layer in tmx_data.layers:
            if not isinstance(layer, TiledTileLayer):
                continue

            if layer.name == self.BUILDABLE_LAYER:
                self._draw_free_build_markers(
                    surface,
                    game_map,
                    layer,
                )
                continue

            if layer.name not in self.DRAW_LAYERS:
                continue

            self._draw_layer(surface, game_map, layer)

    def build_marker_is_visible(
        self,
        game_map: GameMap,
        zone_id: int,
    ) -> bool:
        zone = game_map.build_zones.get(zone_id)

        if zone is None:
            return False

        return not zone.cells.intersection(game_map.occupied_cells)

    def _draw_layer(
        self,
        surface: pygame.Surface,
        game_map: GameMap,
        layer: TiledTileLayer,
    ) -> None:
        for x, y, image in layer.tiles():
            if image is None:
                continue

            self._blit_tile(surface, game_map, x, y, image)

    def _draw_free_build_markers(
        self,
        surface: pygame.Surface,
        game_map: GameMap,
        layer: TiledTileLayer,
    ) -> None:
        images_by_cell = {
            (y, x): image
            for x, y, image in layer.tiles()
            if image is not None
        }

        for zone_id in sorted(game_map.build_zones):
            if not self.build_marker_is_visible(game_map, zone_id):
                continue

            zone = game_map.build_zones[zone_id]
            marker_cell = next(
                (
                    cell
                    for cell in sorted(zone.cells, reverse=True)
                    if cell in images_by_cell
                ),
                None,
            )

            if marker_cell is None:
                self._draw_marker_fallback(surface, game_map, zone_id)
                continue

            row, col = marker_cell
            self._blit_tile(
                surface,
                game_map,
                col,
                row,
                images_by_cell[marker_cell],
            )

    def _draw_marker_fallback(
        self,
        surface: pygame.Surface,
        game_map: GameMap,
        zone_id: int,
    ) -> None:
        zone = game_map.build_zones[zone_id]
        size = game_map.tile_size
        rows = [row for row, _ in zone.cells]
        cols = [col for _, col in zone.cells]
        rect = pygame.Rect(
            min(cols) * size,
            min(rows) * size,
            size * 2,
            size * 2,
        )
        pygame.draw.rect(surface, (228, 194, 79), rect, width=2)

    @staticmethod
    def _blit_tile(
        surface: pygame.Surface,
        game_map: GameMap,
        x: int,
        y: int,
        image: pygame.Surface,
    ) -> None:
        draw_x = x * game_map.tile_size
        draw_y = (y + 1) * game_map.tile_size - image.get_height()
        surface.blit(image, (draw_x, draw_y))

    def _load_tmx(self, game_map: GameMap) -> Any:
        map_path = game_map.tmx_path.resolve()

        if (
            self._tmx_data is not None
            and self._loaded_path == map_path
        ):
            return self._tmx_data

        tmx_data = load_pygame(str(map_path))

        if tmx_data.width != game_map.cols:
            raise ValueError("Ширина TMX не совпадает с GameMap.")

        if tmx_data.height != game_map.rows:
            raise ValueError("Высота TMX не совпадает с GameMap.")

        if tmx_data.tilewidth != game_map.tile_size:
            raise ValueError("Размер тайла TMX не совпадает с GameMap.")

        if tmx_data.tileheight != game_map.tile_size:
            raise ValueError("Размер тайла TMX не совпадает с GameMap.")

        self._tmx_data = tmx_data
        self._loaded_path = map_path
        return tmx_data

    def _draw_fallback(
        self,
        surface: pygame.Surface,
        game_map: GameMap,
    ) -> None:
        size = game_map.tile_size

        for row in range(game_map.rows):
            for col in range(game_map.cols):
                cell = (row, col)
                rect = pygame.Rect(
                    col * size,
                    row * size,
                    size,
                    size,
                )
                tile = game_map.tile_at(cell)

                if tile in {
                    TileKind.ROAD,
                    TileKind.SPAWN,
                    TileKind.GOAL,
                }:
                    color = (182, 122, 76)
                else:
                    color = (89, 143, 75)

                pygame.draw.rect(surface, color, rect)

        for zone_id in sorted(game_map.build_zones):
            if self.build_marker_is_visible(game_map, zone_id):
                self._draw_marker_fallback(surface, game_map, zone_id)
