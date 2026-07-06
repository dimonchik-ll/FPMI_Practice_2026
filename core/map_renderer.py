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
        "Buildable",
    }

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

            if layer.name not in self.DRAW_LAYERS:
                continue

            for x, y, image in layer.tiles():
                if image is None:
                    continue

                draw_x = x * game_map.tile_size
                draw_y = (
                    (y + 1) * game_map.tile_size
                    - image.get_height()
                )

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

                if tile == TileKind.BUILD_SLOT:
                    pygame.draw.rect(
                        surface,
                        (228, 194, 79),
                        rect,
                        width=2,
                    )