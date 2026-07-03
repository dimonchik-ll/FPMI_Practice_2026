from __future__ import annotations

from dataclasses import dataclass, field

from core.map_model import GameMap
from shared.contracts import BuildRequest, GridCell, Vector2


@dataclass(slots=True)
class CoreWorld:
    game_map: GameMap = field(default_factory=GameMap.create_default)

    def route(self) -> tuple[Vector2, ...]:
        return self.game_map.build_route()

    def create_build_request(self, cell: GridCell, tower_kind) -> BuildRequest | None:
        if not self.game_map.is_buildable(cell):
            return None
        return BuildRequest(
            tower_kind=tower_kind,
            cell=cell,
            position=self.game_map.cell_center(cell),
        )

    def confirm_build(self, cell: GridCell) -> bool:
        return self.game_map.occupy(cell)

    def cancel_build(self, cell: GridCell) -> None:
        self.game_map.release(cell)
