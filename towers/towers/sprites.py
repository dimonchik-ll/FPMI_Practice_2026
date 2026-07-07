from __future__ import annotations

from math import atan2, degrees
from typing import Any

from shared.asset_manifest import ARROW_SHEET, TOWER_IDLE_ASSETS, TOWER_UNIT_SHEETS
from shared.assets import load_image
from towers.models import Projectile, TowerRuntime


_BASE_FRAME_WIDTH = 70
_BASE_FRAME_HEIGHT = 130
_UNIT_FRAME_SIZE = 48
_ARROW_RENDER_HEIGHT = 22
_ARROW_SOURCE_OFFSET = -90.0


class TowerRenderer:
    """Рисует пиксельные PNG-кадры без сжатия целых спрайт-листов."""

    def __init__(self) -> None:
        self._base_frames: dict[tuple[object, int], Any] = {}
        self._unit_frames: dict[tuple[object, bool, int], Any] = {}
        self._arrow_frame: Any | None = None
        self._arrow_was_loaded = False

    def draw_tower(self, surface: Any, tower: TowerRuntime) -> None:
        import pygame

        x = int(tower.request.position.x)
        y = int(tower.request.position.y)

        base_frame = self._load_base_frame(tower)
        if base_frame is not None:
            surface.blit(base_frame, base_frame.get_rect(midbottom=(x, y + 32)))

        unit_frame = self._load_unit_frame(tower)
        if unit_frame is not None:
            surface.blit(unit_frame, unit_frame.get_rect(midbottom=(x, y + 10)))

        self._draw_level_badge(surface, tower.level, x + 25, y - 35)

    def draw_projectile(self, surface: Any, projectile: Projectile) -> None:
        import pygame

        x = int(projectile.position.x)
        y = int(projectile.position.y)
        arrow = self._load_arrow_frame()
        if arrow is not None:
            angle = (
                -degrees(atan2(projectile.direction.y, projectile.direction.x))
                + _ARROW_SOURCE_OFFSET
            )
            rotated = pygame.transform.rotate(arrow, angle)
            surface.blit(rotated, rotated.get_rect(center=(x, y)))
            return

        end_x = int(x + projectile.direction.x * 12)
        end_y = int(y + projectile.direction.y * 12)
        pygame.draw.line(surface, (244, 218, 130), (x, y), (end_x, end_y), 2)

    def _load_base_frame(self, tower: TowerRuntime) -> Any | None:
        sheet = load_image(TOWER_IDLE_ASSETS[tower.kind])
        if sheet is None:
            return None

        frame_count = max(1, sheet.get_width() // _BASE_FRAME_WIDTH)
        frame_index = int(tower.animation_time * 5) % frame_count
        cache_key = (tower.kind, frame_index)
        cached = self._base_frames.get(cache_key)
        if cached is not None:
            return cached

        frame = self._frame_from_sheet(
            sheet,
            frame_width=_BASE_FRAME_WIDTH,
            frame_height=_BASE_FRAME_HEIGHT,
            frame_index=frame_index,
        )
        if frame is not None:
            self._base_frames[cache_key] = frame
        return frame

    def _load_unit_frame(self, tower: TowerRuntime) -> Any | None:
        is_attacking = tower.attack_animation_remaining > 0.0
        idle_path = TOWER_UNIT_SHEETS[tower.kind]
        sheet = load_image(self._attack_sheet_path(idle_path)) if is_attacking else None
        if sheet is None:
            sheet = load_image(idle_path)
            is_attacking = False
        if sheet is None:
            return None

        frame_count = max(1, sheet.get_width() // _UNIT_FRAME_SIZE)
        frames_per_second = 12 if is_attacking else 6
        frame_index = int(tower.animation_time * frames_per_second) % frame_count
        cache_key = (tower.kind, is_attacking, frame_index)
        cached = self._unit_frames.get(cache_key)
        if cached is not None:
            return cached

        frame = self._frame_from_sheet(
            sheet,
            frame_width=_UNIT_FRAME_SIZE,
            frame_height=_UNIT_FRAME_SIZE,
            frame_index=frame_index,
        )
        if frame is not None:
            self._unit_frames[cache_key] = frame
        return frame

    @staticmethod
    def _attack_sheet_path(idle_path):
        return idle_path.with_name(idle_path.name.replace("_idle", "_attack"))

    @staticmethod
    def _frame_from_sheet(
        sheet: Any,
        *,
        frame_width: int,
        frame_height: int,
        frame_index: int,
    ) -> Any | None:
        if frame_width <= 0 or frame_height <= 0:
            return None
        if sheet.get_width() < frame_width or sheet.get_height() < frame_height:
            return None

        import pygame

        columns = max(1, sheet.get_width() // frame_width)
        index = frame_index % columns
        rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
        if not sheet.get_rect().contains(rect):
            return None
        return sheet.subsurface(rect).copy()

    def _load_arrow_frame(self) -> Any | None:
        if self._arrow_was_loaded:
            return self._arrow_frame

        self._arrow_was_loaded = True
        arrow = load_image(ARROW_SHEET)
        if arrow is None:
            return None

        width, height = arrow.get_size()
        if width <= 0 or height <= 0:
            return None

        target_height = _ARROW_RENDER_HEIGHT
        target_width = max(1, round(width * target_height / height))

        import pygame

        # arrow_1.png уже является отдельной стрелой 3x14, а не sheet.
        # Обычный scale сохраняет чёткие грани пиксельного ассета.
        self._arrow_frame = pygame.transform.scale(
            arrow,
            (target_width, target_height),
        )
        return self._arrow_frame

    @staticmethod
    def _draw_level_badge(surface: Any, level: int, x: int, y: int) -> None:
        import pygame

        badge = pygame.font.Font(None, 19).render(str(level), True, (255, 248, 205))
        badge_rect = badge.get_rect(center=(x, y))
        background = badge_rect.inflate(7, 5)
        pygame.draw.rect(surface, (43, 45, 58), background, border_radius=4)
        surface.blit(badge, badge_rect)
