from pygame import Vector2
from constants import TILE_SIZE

class Path():
    def __init__(self, tiles: list[Vector2]) -> None:
        self._waypoints = [
            self._tile_to_world(t) for t in tiles
        ]

    def _tile_to_world(self, tile):
        x, y = tile
        return Vector2(
            x * TILE_SIZE + TILE_SIZE / 2,
            y * TILE_SIZE + TILE_SIZE / 2
        )

    def __getitem__(self, index : int) -> Vector2:
        return self._waypoints[index]

    def __len__(self) -> int:
        return len(self._waypoints)