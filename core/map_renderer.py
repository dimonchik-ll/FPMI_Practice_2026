from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import pygame

from core.map_model import GameMap
from shared.contracts import TileKind


FLIPPED_HORIZONTALLY_FLAG = 0x80000000
FLIPPED_VERTICALLY_FLAG = 0x40000000
FLIPPED_DIAGONALLY_FLAG = 0x20000000
ROTATED_HEXAGONAL_120_FLAG = 0x10000000

GID_FLAG_MASK = (
    FLIPPED_HORIZONTALLY_FLAG
    | FLIPPED_VERTICALLY_FLAG
    | FLIPPED_DIAGONALLY_FLAG
    | ROTATED_HEXAGONAL_120_FLAG
)


@dataclass(frozen=True)
class AnimationFrame:
    gid: int
    duration: int


@dataclass(frozen=True)
class TileLayerData:
    name: str
    width: int
    height: int
    visible: bool
    gids: list[list[int]]


class MapRenderer:
    DRAW_LAYERS = {
        "ground",
        "road",
        "shadow",
        "stone",
        "bush",
        "tree",
        "camp",
        "decor",
        "dirt",
    }

    BUILDABLE_LAYER = "buildable"

    def __init__(self) -> None:
        self._loaded_path: Path | None = None
        self._tile_layers: list[TileLayerData] = []
        self._tile_images: dict[int, pygame.Surface] = {}
        self._animations: dict[int, tuple[AnimationFrame, ...]] = {}

    def draw(
        self,
        surface: pygame.Surface,
        game_map: GameMap,
    ) -> None:
        if game_map.tmx_path is None:
            self._draw_fallback(surface, game_map)
            return

        self._load_map_if_needed(game_map)

        for layer in self._tile_layers:
            if not layer.visible:
                continue

            layer_key = self._normalize_layer_name(layer.name)

            if layer_key == self.BUILDABLE_LAYER:
                self._draw_free_build_markers(
                    surface,
                    game_map,
                    layer,
                )
                continue

            if layer_key not in self.DRAW_LAYERS:
                continue

            self._draw_layer(
                surface,
                game_map,
                layer,
            )

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
        layer: TileLayerData,
    ) -> None:
        for y, row in enumerate(layer.gids):
            for x, raw_gid in enumerate(row):
                if raw_gid == 0:
                    continue

                image = self._get_tile_image(raw_gid)

                if image is None:
                    continue

                self._blit_tile(
                    surface,
                    game_map,
                    x,
                    y,
                    image,
                )

    def _draw_free_build_markers(
        self,
        surface: pygame.Surface,
        game_map: GameMap,
        layer: TileLayerData,
    ) -> None:
        for zone_id in sorted(game_map.build_zones):
            if not self.build_marker_is_visible(game_map, zone_id):
                continue

            zone = game_map.build_zones[zone_id]

            for row, col in sorted(zone.cells):
                if row >= layer.height or col >= layer.width:
                    continue

                raw_gid = layer.gids[row][col]

                if raw_gid == 0:
                    continue

                image = self._get_tile_image(raw_gid)

                if image is None:
                    continue

                self._blit_tile(
                    surface,
                    game_map,
                    col,
                    row,
                    image,
                )

    def _get_tile_image(
        self,
        raw_gid: int,
    ) -> pygame.Surface | None:
        clean_gid = raw_gid & ~GID_FLAG_MASK

        animation = self._animations.get(clean_gid)

        if animation:
            image = self._get_current_animation_frame(animation)
        else:
            image = self._tile_images.get(clean_gid)

        if image is None:
            return None

        return self._apply_gid_flags(
            image,
            raw_gid,
        )

    def _get_current_animation_frame(
        self,
        frames: tuple[AnimationFrame, ...],
    ) -> pygame.Surface | None:
        total_duration = sum(frame.duration for frame in frames)

        if total_duration <= 0:
            return None

        current_time = pygame.time.get_ticks() % total_duration
        passed_time = 0

        for frame in frames:
            passed_time += frame.duration

            if current_time < passed_time:
                return self._tile_images.get(frame.gid)

        return self._tile_images.get(frames[-1].gid)

    def _apply_gid_flags(
        self,
        image: pygame.Surface,
        raw_gid: int,
    ) -> pygame.Surface:
        flip_horizontal = bool(raw_gid & FLIPPED_HORIZONTALLY_FLAG)
        flip_vertical = bool(raw_gid & FLIPPED_VERTICALLY_FLAG)
        flip_diagonal = bool(raw_gid & FLIPPED_DIAGONALLY_FLAG)

        if not (
            flip_horizontal
            or flip_vertical
            or flip_diagonal
        ):
            return image

        result = image

        if flip_diagonal:
            result = pygame.transform.rotate(result, 90)
            result = pygame.transform.flip(result, True, False)

        if flip_horizontal or flip_vertical:
            result = pygame.transform.flip(
                result,
                flip_horizontal,
                flip_vertical,
            )

        return result

    def _blit_tile(
        self,
        surface: pygame.Surface,
        game_map: GameMap,
        x: int,
        y: int,
        image: pygame.Surface,
    ) -> None:
        draw_x = x * game_map.tile_size
        draw_y = (
            (y + 1) * game_map.tile_size
            - image.get_height()
        )

        surface.blit(image, (draw_x, draw_y))

    def _load_map_if_needed(
        self,
        game_map: GameMap,
    ) -> None:
        if game_map.tmx_path is None:
            return

        map_path = game_map.tmx_path.resolve()

        if self._loaded_path == map_path:
            return

        root = ET.parse(map_path).getroot()

        map_width = int(root.attrib["width"])
        map_height = int(root.attrib["height"])
        tile_width = int(root.attrib["tilewidth"])
        tile_height = int(root.attrib["tileheight"])

        if map_width != game_map.cols:
            raise ValueError("Ширина TMX не совпадает с GameMap.")

        if map_height != game_map.rows:
            raise ValueError("Высота TMX не совпадает с GameMap.")

        if tile_width != game_map.tile_size:
            raise ValueError("Ширина тайла TMX не совпадает с GameMap.")

        if tile_height != game_map.tile_size:
            raise ValueError("Высота тайла TMX не совпадает с GameMap.")

        self._tile_images = {}
        self._animations = {}
        self._tile_layers = []

        self._load_tilesets(
            root,
            map_path,
        )

        self._tile_layers = self._load_tile_layers(root)

        self._loaded_path = map_path

    def _load_tilesets(
        self,
        map_root: ET.Element,
        map_path: Path,
    ) -> None:
        for tileset_element in map_root.findall("tileset"):
            first_gid = int(tileset_element.attrib["firstgid"])
            source = tileset_element.attrib.get("source")

            if source is None:
                tileset_root = tileset_element
                tileset_path = map_path
            else:
                tileset_path = (map_path.parent / source).resolve()
                tileset_root = ET.parse(tileset_path).getroot()

            self._load_tileset_images(
                first_gid,
                tileset_root,
                tileset_path.parent,
            )

            self._load_tileset_animations(
                first_gid,
                tileset_root,
            )

    def _load_tileset_images(
        self,
        first_gid: int,
        tileset_root: ET.Element,
        tileset_dir: Path,
    ) -> None:
        tile_width = int(tileset_root.attrib["tilewidth"])
        tile_height = int(tileset_root.attrib["tileheight"])
        spacing = int(tileset_root.attrib.get("spacing", "0"))
        margin = int(tileset_root.attrib.get("margin", "0"))

        image_element = tileset_root.find("image")

        if image_element is not None:
            self._load_tileset_sheet(
                first_gid,
                tileset_root,
                image_element,
                tileset_dir,
                tile_width,
                tile_height,
                spacing,
                margin,
            )

        for tile_element in tileset_root.findall("tile"):
            tile_id = int(tile_element.attrib["id"])
            tile_image = tile_element.find("image")

            if tile_image is None:
                continue

            source = tile_image.attrib["source"]
            image_path = (tileset_dir / source).resolve()
            image = pygame.image.load(str(image_path)).convert_alpha()

            self._tile_images[first_gid + tile_id] = image

    def _load_tileset_sheet(
        self,
        first_gid: int,
        tileset_root: ET.Element,
        image_element: ET.Element,
        tileset_dir: Path,
        tile_width: int,
        tile_height: int,
        spacing: int,
        margin: int,
    ) -> None:
        source = image_element.attrib["source"]
        image_path = (tileset_dir / source).resolve()
        sheet = pygame.image.load(str(image_path)).convert_alpha()

        columns = int(
            tileset_root.attrib.get(
                "columns",
                max(1, sheet.get_width() // tile_width),
            )
        )

        tile_count = int(
            tileset_root.attrib.get(
                "tilecount",
                columns * max(1, sheet.get_height() // tile_height),
            )
        )

        for tile_id in range(tile_count):
            col = tile_id % columns
            row = tile_id // columns

            x = margin + col * (tile_width + spacing)
            y = margin + row * (tile_height + spacing)

            rect = pygame.Rect(
                x,
                y,
                tile_width,
                tile_height,
            )

            if not sheet.get_rect().contains(rect):
                continue

            self._tile_images[first_gid + tile_id] = sheet.subsurface(
                rect,
            ).copy()

    def _load_tileset_animations(
        self,
        first_gid: int,
        tileset_root: ET.Element,
    ) -> None:
        for tile_element in tileset_root.findall("tile"):
            animation = tile_element.find("animation")

            if animation is None:
                continue

            tile_id = int(tile_element.attrib["id"])
            base_gid = first_gid + tile_id
            frames: list[AnimationFrame] = []

            for frame_element in animation.findall("frame"):
                frame_tile_id = int(frame_element.attrib["tileid"])
                duration = int(
                    frame_element.attrib.get(
                        "duration",
                        "100",
                    )
                )

                frames.append(
                    AnimationFrame(
                        gid=first_gid + frame_tile_id,
                        duration=duration,
                    )
                )

            if frames:
                self._animations[base_gid] = tuple(frames)

    def _load_tile_layers(
        self,
        map_root: ET.Element,
    ) -> list[TileLayerData]:
        layers: list[TileLayerData] = []

        for layer_element in map_root.findall("layer"):
            data_element = layer_element.find("data")

            if data_element is None:
                continue

            name = layer_element.attrib["name"]
            width = int(layer_element.attrib["width"])
            height = int(layer_element.attrib["height"])
            visible = layer_element.attrib.get("visible", "1") != "0"

            values = self._read_layer_values(data_element)

            if len(values) != width * height:
                raise ValueError(
                    f"Слой {name} содержит {len(values)} тайлов, "
                    f"ожидалось {width * height}."
                )

            gids = [
                values[row * width : (row + 1) * width]
                for row in range(height)
            ]

            layers.append(
                TileLayerData(
                    name=name,
                    width=width,
                    height=height,
                    visible=visible,
                    gids=gids,
                )
            )

        return layers

    def _read_layer_values(
        self,
        data_element: ET.Element,
    ) -> list[int]:
        encoding = data_element.attrib.get("encoding")

        if encoding == "csv":
            return [
                int(value.strip())
                for value in (data_element.text or "")
                .replace("\n", "")
                .split(",")
                if value.strip()
            ]

        if encoding is None:
            return [
                int(tile.attrib.get("gid", "0"))
                for tile in data_element.findall("tile")
            ]

        raise ValueError(
            f"Неподдерживаемый формат слоя TMX: encoding={encoding}. "
            "Сохрани карту в Tiled с форматом CSV."
        )

    def _normalize_layer_name(
        self,
        name: str,
    ) -> str:
        return (
            name.strip()
            .replace("С", "C")
            .replace("с", "c")
            .lower()
        )

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
            if not self.build_marker_is_visible(game_map, zone_id):
                continue

            zone = game_map.build_zones[zone_id]
            rows = [row for row, _ in zone.cells]
            cols = [col for _, col in zone.cells]

            rect = pygame.Rect(
                min(cols) * size,
                min(rows) * size,
                size * 2,
                size * 2,
            )

            pygame.draw.rect(
                surface,
                (228, 194, 79),
                rect,
                width=2,
            )