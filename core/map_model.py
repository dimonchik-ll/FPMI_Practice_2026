from __future__ import annotations

from core.levels import get_level_path

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET

from shared.contracts import GridCell, TileKind, Vector2



GID_MASK = 0x0FFFFFFF


@dataclass(frozen=True, slots=True)
class BuildZone:
    zone_id: int
    cells: frozenset[GridCell]
    center: Vector2


@dataclass(slots=True)
class GameMap:
    tiles: list[list[TileKind]]
    tile_size: int = 32
    occupied_cells: set[GridCell] = field(default_factory=set)

    tmx_path: Path | None = None
    road_cells: frozenset[GridCell] = field(default_factory=frozenset)
    spawn_cells: frozenset[GridCell] = field(default_factory=frozenset)
    base_cells: frozenset[GridCell] = field(default_factory=frozenset)
    build_zones: dict[int, BuildZone] = field(default_factory=dict)

    _zone_by_cell: dict[GridCell, BuildZone] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not self.tiles or not self.tiles[0]:
            raise ValueError("Карта не может быть пустой.")

        width = len(self.tiles[0])

        if any(len(row) != width for row in self.tiles):
            raise ValueError("Все строки карты должны иметь одинаковую длину.")

        for zone in self.build_zones.values():
            for cell in zone.cells:
                if not self.is_inside(cell):
                    raise ValueError(
                        f"Зона строительства {zone.zone_id} вне карты: {cell}."
                    )

                if cell in self._zone_by_cell:
                    raise ValueError(
                        f"Клетка {cell} принадлежит нескольким зонам."
                    )

                self._zone_by_cell[cell] = zone

    @classmethod
    def create_default(cls) -> "GameMap":
        return cls.create_from_level(1)

    @classmethod
    def create_from_level(cls, level_number: int) -> "GameMap":
        return cls.create_from_tmx(get_level_path(level_number))

    @classmethod
    def create_from_tmx(cls, map_path: str | Path) -> "GameMap":
        path = Path(map_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Карта не найдена: {path}")

        root = ET.parse(path).getroot()

        width = cls._read_int_attribute(root, "width")
        height = cls._read_int_attribute(root, "height")
        tile_width = cls._read_int_attribute(root, "tilewidth")
        tile_height = cls._read_int_attribute(root, "tileheight")

        if root.get("orientation") != "orthogonal":
            raise ValueError("Поддерживаются только orthogonal-карты.")

        if tile_width != tile_height:
            raise ValueError("Клетки карты должны быть квадратными.")

        road_layer = cls._find_layer(root, "Road")
        road_cells = cls._load_layer_cells(
            layer=road_layer,
            width=width,
            height=height,
        )

        objects_layer = cls._find_object_group(root, "Objects")
        markers = cls._load_markers(
            object_group=objects_layer,
            tile_size=tile_width,
        )

        spawn_cells = markers["spawn"]
        base_cells = markers["base"]

        if not spawn_cells.intersection(road_cells):
            raise ValueError("spawn должен пересекаться с дорогой.")

        if not base_cells.intersection(road_cells):
            raise ValueError("base должен пересекаться с дорогой.")

        build_zone_layer = cls._find_object_group(root, "BuildZone")
        build_zones = cls._load_build_zones(
            object_group=build_zone_layer,
            tile_size=tile_width,
            width=width,
            height=height,
            road_cells=road_cells,
            spawn_cells=spawn_cells,
            base_cells=base_cells,
        )

        tiles = [
            [TileKind.GRASS for _ in range(width)]
            for _ in range(height)
        ]

        for row, col in road_cells:
            tiles[row][col] = TileKind.ROAD

        for zone in build_zones.values():
            for row, col in zone.cells:
                tiles[row][col] = TileKind.BUILD_SLOT

        for row, col in spawn_cells:
            tiles[row][col] = TileKind.SPAWN

        for row, col in base_cells:
            tiles[row][col] = TileKind.GOAL

        return cls(
            tiles=tiles,
            tile_size=tile_width,
            tmx_path=path,
            road_cells=frozenset(road_cells),
            spawn_cells=spawn_cells,
            base_cells=base_cells,
            build_zones=build_zones,
        )

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
        if not self.is_inside(cell):
            return TileKind.BLOCKED

        row, col = cell
        return self.tiles[row][col]

    def world_to_cell(self, position: Vector2) -> GridCell:
        return (
            int(position.y // self.tile_size),
            int(position.x // self.tile_size),
        )

    def cell_center(self, cell: GridCell) -> Vector2:
        zone = self.get_build_zone(cell)

        if zone is not None:
            return zone.center

        row, col = cell

        return Vector2(
            x=col * self.tile_size + self.tile_size / 2,
            y=row * self.tile_size + self.tile_size / 2,
        )

    def get_build_zone(self, cell: GridCell) -> BuildZone | None:
        return self._zone_by_cell.get(cell)

    def is_buildable(self, cell: GridCell) -> bool:
        zone = self.get_build_zone(cell)

        if zone is not None:
            return not zone.cells.intersection(self.occupied_cells)

        return (
            self.tile_at(cell) == TileKind.BUILD_SLOT
            and cell not in self.occupied_cells
        )

    def occupy(self, cell: GridCell) -> bool:
        if not self.is_buildable(cell):
            return False

        zone = self.get_build_zone(cell)

        if zone is not None:
            self.occupied_cells.update(zone.cells)
            return True

        self.occupied_cells.add(cell)
        return True

    def release(self, cell: GridCell) -> None:
        zone = self.get_build_zone(cell)

        if zone is not None:
            self.occupied_cells.difference_update(zone.cells)
            return

        self.occupied_cells.discard(cell)

    def build_route(self) -> tuple[Vector2, ...]:
        if self.road_cells and self.spawn_cells and self.base_cells:
            return self._build_tmx_route()

        return self._build_legacy_route()

    def _build_tmx_route(self) -> tuple[Vector2, ...]:
        start_cells = sorted(self.spawn_cells.intersection(self.road_cells))
        goal_cells = self.base_cells.intersection(self.road_cells)

        if not start_cells or not goal_cells:
            return ()

        queue: deque[GridCell] = deque(start_cells)
        previous: dict[GridCell, GridCell | None] = {
            cell: None
            for cell in start_cells
        }

        target: GridCell | None = None

        while queue:
            cell = queue.popleft()

            if cell in goal_cells:
                target = cell
                break

            row, col = cell

            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in previous:
                    continue

                if neighbor not in self.road_cells:
                    continue

                previous[neighbor] = cell
                queue.append(neighbor)

        if target is None:
            return ()

        route_cells: list[GridCell] = []

        while target is not None:
            route_cells.append(target)
            target = previous[target]

        route_cells.reverse()

        return tuple(
            self._plain_cell_center(cell)
            for cell in route_cells
        )

    def _build_legacy_route(self) -> tuple[Vector2, ...]:
        start = self._find(TileKind.SPAWN)
        goal = self._find(TileKind.GOAL)

        if start is None or goal is None:
            return ()

        allowed = {
            TileKind.SPAWN,
            TileKind.ROAD,
            TileKind.GOAL,
        }

        queue: deque[GridCell] = deque([start])
        previous: dict[GridCell, GridCell | None] = {start: None}

        while queue:
            cell = queue.popleft()

            if cell == goal:
                break

            row, col = cell

            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
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

        return tuple(
            self.cell_center(cell)
            for cell in route_cells
        )

    def _plain_cell_center(self, cell: GridCell) -> Vector2:
        row, col = cell

        return Vector2(
            x=col * self.tile_size + self.tile_size / 2,
            y=row * self.tile_size + self.tile_size / 2,
        )

    def _find(self, target: TileKind) -> GridCell | None:
        for row_index, row in enumerate(self.tiles):
            for col_index, tile in enumerate(row):
                if tile == target:
                    return row_index, col_index

        return None

    @staticmethod
    def _read_int_attribute(
        element: ET.Element,
        attribute_name: str,
    ) -> int:
        value = element.get(attribute_name)

        if value is None:
            raise ValueError(
                f"Нет атрибута {attribute_name}."
            )

        return int(value)

    @staticmethod
    def _find_layer(
        root: ET.Element,
        layer_name: str,
    ) -> ET.Element:
        for layer in root.findall("layer"):
            if layer.get("name") == layer_name:
                return layer

        raise ValueError(f"Не найден Tile Layer '{layer_name}'.")

    @staticmethod
    def _find_object_group(
        root: ET.Element,
        group_name: str,
    ) -> ET.Element:
        for group in root.findall("objectgroup"):
            if group.get("name") == group_name:
                return group

        raise ValueError(f"Не найден Object Layer '{group_name}'.")

    @classmethod
    def _load_layer_cells(
        cls,
        layer: ET.Element,
        width: int,
        height: int,
    ) -> set[GridCell]:
        data = layer.find("data")

        if data is None or data.get("encoding") != "csv":
            raise ValueError(
                f"Слой '{layer.get('name')}' должен использовать CSV."
            )

        values = [
            value.strip()
            for value in (data.text or "").split(",")
            if value.strip()
        ]

        if len(values) != width * height:
            raise ValueError(
                f"В слое '{layer.get('name')}' неверное количество тайлов."
            )

        cells: set[GridCell] = set()

        for index, value in enumerate(values):
            gid = int(value) & GID_MASK

            if gid == 0:
                continue

            row = index // width
            col = index % width
            cells.add((row, col))

        return cells

    @classmethod
    def _load_markers(
        cls,
        object_group: ET.Element,
        tile_size: int,
    ) -> dict[str, frozenset[GridCell]]:
        markers: dict[str, frozenset[GridCell]] = {}

        for obj in object_group.findall("object"):
            marker_type = obj.get("type")

            if marker_type not in {"spawn", "base"}:
                continue

            if marker_type in markers:
                raise ValueError(
                    f"На карте больше одного объекта '{marker_type}'."
                )

            x, y, width, height = cls._object_rect(obj)

            markers[marker_type] = frozenset(
                cls._rect_to_cells(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    tile_size=tile_size,
                )
            )

        for marker_type in ("spawn", "base"):
            if marker_type not in markers:
                raise ValueError(
                    f"В слое Objects нет '{marker_type}'."
                )

        return markers

    @classmethod
    def _load_build_zones(
        cls,
        object_group: ET.Element,
        tile_size: int,
        width: int,
        height: int,
        road_cells: set[GridCell],
        spawn_cells: frozenset[GridCell],
        base_cells: frozenset[GridCell],
    ) -> dict[int, BuildZone]:
        zones: dict[int, BuildZone] = {}
        used_cells: set[GridCell] = set()

        for obj in object_group.findall("object"):
            if obj.get("type") != "tower_spot":
                continue

            zone_id = cls._read_zone_id(obj)

            if zone_id in zones:
                raise ValueError(f"Повторяется zone_id={zone_id}.")

            x, y, zone_width, zone_height = cls._object_rect(obj)

            if (
                zone_width != tile_size * 2
                or zone_height != tile_size * 2
            ):
                raise ValueError(
                    f"Зона {zone_id} должна быть 2×2 клетки."
                )

            cells = cls._rect_to_cells(
                x=x,
                y=y,
                width=zone_width,
                height=zone_height,
                tile_size=tile_size,
            )

            if len(cells) != 4:
                raise ValueError(
                    f"Зона {zone_id} должна покрывать 4 клетки."
                )

            if any(
                row < 0
                or row >= height
                or col < 0
                or col >= width
                for row, col in cells
            ):
                raise ValueError(
                    f"Зона {zone_id} выходит за карту."
                )

            if cells.intersection(road_cells):
                raise ValueError(
                    f"Зона {zone_id} пересекается с дорогой."
                )

            if cells.intersection(spawn_cells):
                raise ValueError(
                    f"Зона {zone_id} пересекается со spawn."
                )

            if cells.intersection(base_cells):
                raise ValueError(
                    f"Зона {zone_id} пересекается с base."
                )

            if cells.intersection(used_cells):
                raise ValueError(
                    f"Зона {zone_id} пересекается с другой зоной."
                )

            used_cells.update(cells)

            zones[zone_id] = BuildZone(
                zone_id=zone_id,
                cells=frozenset(cells),
                center=Vector2(
                    x=x + zone_width / 2,
                    y=y + zone_height / 2,
                ),
            )

        if not zones:
            raise ValueError(
                "В BuildZone нет объектов tower_spot."
            )

        return zones

    @staticmethod
    def _read_zone_id(obj: ET.Element) -> int:
        properties = obj.find("properties")

        if properties is None:
            raise ValueError(
                f"У объекта '{obj.get('name')}' нет zone_id."
            )

        for prop in properties.findall("property"):
            if prop.get("name") != "zone_id":
                continue

            value = prop.get("value") or prop.text

            if value is not None:
                return int(value)

        raise ValueError(
            f"У объекта '{obj.get('name')}' нет zone_id."
        )

    @staticmethod
    def _object_rect(
        obj: ET.Element,
    ) -> tuple[int, int, int, int]:
        values: list[int] = []

        for attribute_name in ("x", "y", "width", "height"):
            value = obj.get(attribute_name)

            if value is None:
                raise ValueError(
                    f"У объекта '{obj.get('name')}' нет {attribute_name}."
                )

            number = float(value)

            if not number.is_integer():
                raise ValueError(
                    f"{attribute_name} объекта '{obj.get('name')}' "
                    "должен быть целым."
                )

            values.append(int(number))

        return values[0], values[1], values[2], values[3]

    @staticmethod
    def _rect_to_cells(
        x: int,
        y: int,
        width: int,
        height: int,
        tile_size: int,
    ) -> set[GridCell]:
        if width <= 0 or height <= 0:
            raise ValueError("Размер объекта должен быть положительным.")

        if (
            x % tile_size != 0
            or y % tile_size != 0
            or width % tile_size != 0
            or height % tile_size != 0
        ):
            raise ValueError(
                "spawn, base и tower_spot должны быть выровнены по сетке."
            )

        left_col = x // tile_size
        top_row = y // tile_size
        right_col = (x + width - 1) // tile_size
        bottom_row = (y + height - 1) // tile_size

        return {
            (row, col)
            for row in range(top_row, bottom_row + 1)
            for col in range(left_col, right_col + 1)
        }