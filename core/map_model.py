from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from shared.contracts import GridCell, TileKind, Vector2

DEFAULT_LEVEL: tuple[tuple[TileKind, ...], ...] = (
    (TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.GRASS, TileKind.GRASS, TileKind.SPAWN, TileKind.ROAD, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.ROAD, TileKind.BUILD_SLOT, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.ROAD, TileKind.ROAD, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BUILD_SLOT, TileKind.ROAD, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BUILD_SLOT, TileKind.GRASS, TileKind.GRASS, TileKind.ROAD, TileKind.ROAD, TileKind.ROAD, TileKind.GOAL, TileKind.GRASS, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.ROAD, TileKind.ROAD, TileKind.ROAD, TileKind.ROAD, TileKind.ROAD, TileKind.ROAD, TileKind.ROAD, TileKind.ROAD, TileKind.BUILD_SLOT, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BUILD_SLOT, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.GRASS, TileKind.BLOCKED),
    (TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED, TileKind.BLOCKED),
)


@dataclass(slots=True)
class GameMap:
    tiles: list[list[TileKind]]
    tile_size: int = 48
    occupied_cells: set[GridCell] = field(default_factory=set)

    @classmethod
    def create_default(cls) -> "GameMap":
        return cls(tiles=[list(row) for row in DEFAULT_LEVEL])

    @property
    def rows(self) -> int:
        return len(self.tiles)

    @property
    def cols(self) -> int:
        return len(self.tiles[0])

    @property
    def pixel_width(self) -> int:
        return self.cols * self.tile_size

    @property
    def pixel_height(self) -> int:
        return self.rows * self.tile_size

    def is_inside(self, cell: GridCell) -> bool:
        row, col = cell
        return 0 <= row < self.rows and 0 <= col < self.cols

    def tile_at(self, cell: GridCell) -> TileKind:
        row, col = cell
        if not self.is_inside(cell):
            return TileKind.BLOCKED
        return self.tiles[row][col]

    def world_to_cell(self, position: Vector2) -> GridCell:
        return int(position.y // self.tile_size), int(position.x // self.tile_size)

    def cell_center(self, cell: GridCell) -> Vector2:
        row, col = cell
        return Vector2(
            x=col * self.tile_size + self.tile_size / 2,
            y=row * self.tile_size + self.tile_size / 2,
        )

    def is_buildable(self, cell: GridCell) -> bool:
        return self.tile_at(cell) == TileKind.BUILD_SLOT and cell not in self.occupied_cells

    def occupy(self, cell: GridCell) -> bool:
        if not self.is_buildable(cell):
            return False
        self.occupied_cells.add(cell)
        return True

    def release(self, cell: GridCell) -> None:
        self.occupied_cells.discard(cell)

    def build_route(self) -> tuple[Vector2, ...]:
        start = self._find(TileKind.SPAWN)
        goal = self._find(TileKind.GOAL)
        if start is None or goal is None:
            return ()

        allowed = {TileKind.SPAWN, TileKind.ROAD, TileKind.GOAL}
        queue: deque[GridCell] = deque([start])
        previous: dict[GridCell, GridCell | None] = {start: None}

        while queue:
            cell = queue.popleft()
            if cell == goal:
                break
            row, col = cell
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in previous:
                    continue
                if self.tile_at(neighbor) not in allowed:
                    continue
                previous[neighbor] = cell
                queue.append(neighbor)

        if goal not in previous:
            return ()

        route_cells: list[GridCell] = []
        cursor: GridCell | None = goal
        while cursor is not None:
            route_cells.append(cursor)
            cursor = previous[cursor]
        route_cells.reverse()
        return tuple(self.cell_center(cell) for cell in route_cells)

    def _find(self, target: TileKind) -> GridCell | None:
        for row_index, row in enumerate(self.tiles):
            for col_index, tile in enumerate(row):
                if tile == target:
                    return row_index, col_index
        return None
