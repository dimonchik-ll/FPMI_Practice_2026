from Map.time_map import TileMap
from Navigation.path import Path
from collections import deque

class PathProvider:

    def __init__(self, tile_map : TileMap):
        self._map = tile_map

    def _find_start(self) -> tuple[int, int]:
        for y in range(self._map.height):
            for x in range(self._map.width):
                if self._map.is_start(x, y):
                    return x, y
        return 0, 0

    def _find_end(self) -> tuple[int, int]:
        for y in range(self._map.height):
            for x in range(self._map.width):
                if self._map.is_end(x, y):
                    return x, y
        return 0, 0

    def build_path(self) -> Path:
        start = self._find_start()
        end = self._find_end()

        queue = deque([start])
        visited = {start}
        came_from: dict[tuple[int, int], tuple[int, int]] = {}

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        found = False

        while queue:
            x, y = queue.popleft()

            if (x, y) == end:
                found = True
                break

            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                if (nx, ny) in visited:
                    continue

                if not self._map.is_walkable(nx, ny):
                    continue

                visited.add((nx, ny))
                came_from[(nx, ny)] = (x, y)
                queue.append((nx, ny))

        if not found:
            return Path([])

        tiles = []
        current = end

        while current != start:
            tiles.append(current)
            current = came_from[current]

        tiles.append(start)
        tiles.reverse()

        return Path(tiles)
