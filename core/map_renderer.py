from __future__ import annotations

import pygame

from core.map_model import GameMap
from shared.asset_manifest import TILE_ASSETS
from shared.assets import load_image
from shared.contracts import TileKind


class MapRenderer:
    def draw(self, surface: pygame.Surface, game_map: GameMap) -> None:
        size = game_map.tile_size
        grass = load_image(TILE_ASSETS["grass"], (size, size))
        road = load_image(TILE_ASSETS["road"], (size, size))
        build_slot = load_image(TILE_ASSETS["build_slot"], (size, size))

        for row in range(game_map.rows):
            for col in range(game_map.cols):
                cell = (row, col)
                rect = pygame.Rect(col * size, row * size, size, size)
                tile = game_map.tile_at(cell)

                if tile == TileKind.BLOCKED:
                    pygame.draw.rect(surface, (56, 75, 56), rect)
                    continue

                if tile in {TileKind.ROAD, TileKind.SPAWN, TileKind.GOAL}:
                    if road is not None:
                        surface.blit(road, rect)
                    else:
                        pygame.draw.rect(surface, (190, 126, 75), rect)
                else:
                    if grass is not None:
                        surface.blit(grass, rect)
                    else:
                        pygame.draw.rect(surface, (107, 160, 80), rect)

                if tile == TileKind.BUILD_SLOT and cell not in game_map.occupied_cells:
                    if build_slot is not None:
                        surface.blit(build_slot, rect)
                    else:
                        pygame.draw.circle(surface, (220, 196, 102), rect.center, size // 3, 2)

                if tile == TileKind.SPAWN:
                    pygame.draw.circle(surface, (82, 149, 221), rect.center, size // 5)
                elif tile == TileKind.GOAL:
                    pygame.draw.circle(surface, (197, 71, 64), rect.center, size // 5)

                pygame.draw.rect(surface, (40, 56, 40), rect, 1)
