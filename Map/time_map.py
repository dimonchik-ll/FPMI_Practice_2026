from typing import List
from constants import TILE_SIZE, COLOR_MAP, BLACK
from pygame import draw, Surface

class TileMap:

    def __init__(self, grid: List[List[int]]):
        self.grid = grid
        self.width = len(self.grid[0])
        self.height = len(self.grid)

    def __getitem__(self, row : int) -> List[int]:
        return self.grid[row]

    def is_walkable(self, x: int, y: int) -> bool:
        return self.grid[y][x] == 0 or self.grid[y][x] == 4 or self.grid[y][x] == 5

    def is_start(self, x: int, y: int) -> bool:
        return self.grid[y][x] == 5

    def is_end(self, x: int, y: int) -> bool:
        return self.grid[y][x] == 4

    def draw(self, scene : Surface):
        for row in range(self.height):
            for col in range(self.width):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                value = self.grid[row][col]

                color = COLOR_MAP.get(value)

                draw.rect(scene, color, (x, y, TILE_SIZE, TILE_SIZE))

                if value == 3:
                    draw.rect(scene, BLACK, (x, y, TILE_SIZE, TILE_SIZE), 1)