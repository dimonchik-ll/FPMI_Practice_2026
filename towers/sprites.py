from __future__ import annotations

from math import atan2, degrees
from pathlib import Path
from typing import Any

from shared.asset_manifest import ARROW_SHEET, TOWER_IDLE_ASSETS, TOWER_UNIT_SHEETS
from shared.assets import load_image
from towers.models import Projectile, TowerRuntime


class TowerRenderer:
    def draw_tower(self, surface: Any, tower: TowerRuntime) -> None:
        import pygame

        x = int(tower.request.position.x)
        y = int(tower.request.position.y)
        base_image = load_image(TOWER_IDLE_ASSETS[tower.kind], (58, 96))

        if base_image is not None:
            base_rect = base_image.get_rect(midbottom=(x, y + 30))
            surface.blit(base_image, base_rect)
        else:
            pygame.draw.circle(surface, (93, 83, 59), (x, y), 19)
            pygame.draw.circle(surface, (239, 212, 128), (x, y), 15, 2)

        unit_frame = self._load_unit_frame(tower)
        if unit_frame is not None:
            unit_rect = unit_frame.get_rect(midbottom=(x, y + 8))
            surface.blit(unit_frame, unit_rect)

        if tower.attack_animation_remaining > 0.0:
            pygame.draw.circle(surface, (255, 225, 126), (x, y - 24), 8, 2)

        badge = pygame.font.Font(None, 19).render(str(tower.level), True, (255, 248, 205))
        badge_rect = badge.get_rect(center=(x + 23, y - 31))
        pygame.draw.circle(surface, (43, 45, 58), badge_rect.center, 9)
        surface.blit(badge, badge_rect)

    def draw_projectile(self, surface: Any, projectile: Projectile) -> None:
        import pygame

        arrow = self._load_arrow_frame()
        x = int(projectile.position.x)
        y = int(projectile.position.y)

        if arrow is not None:
            angle = -degrees(atan2(projectile.direction.y, projectile.direction.x))
            rotated = pygame.transform.rotate(arrow, angle)
            surface.blit(rotated, rotated.get_rect(center=(x, y)))
            return

        end_x = int(x + projectile.direction.x * 12)
        end_y = int(y + projectile.direction.y * 12)
        pygame.draw.line(surface, (244, 218, 130), (x, y), (end_x, end_y), 3)
        pygame.draw.circle(surface, (94, 65, 34), (x, y), 3)

    def _load_unit_frame(self, tower: TowerRuntime) -> Any | None:
        sheet_path = self._sheet_path(tower.kind, tower.attack_animation_remaining > 0.0)
        sheet = load_image(sheet_path)
        if sheet is None:
            return None

        frame = self._frame_from_sheet(sheet, tower.animation_time, tower.attack_animation_remaining > 0.0)
        if frame is None:
            return None

        import pygame

        return pygame.transform.scale(frame, (38, 38))

    @staticmethod
    def _sheet_path(kind, is_attacking: bool) -> Path:
        idle_path = TOWER_UNIT_SHEETS[kind]
        if not is_attacking:
            return idle_path
        return idle_path.with_name(idle_path.name.replace("_idle", "_attack"))

    @staticmethod
    def _frame_from_sheet(sheet: Any, animation_time: float, is_attacking: bool) -> Any | None:
        import pygame

        frame_size = sheet.get_height()
        if frame_size <= 0:
            return None
        frame_count = max(1, sheet.get_width() // frame_size)
        frames_per_second = 12 if is_attacking else 6
        frame_index = int(animation_time * frames_per_second) % frame_count
        rect = pygame.Rect(frame_index * frame_size, 0, frame_size, frame_size)
        if not sheet.get_rect().contains(rect):
            return None
        return sheet.subsurface(rect).copy()

    @staticmethod
    def _load_arrow_frame() -> Any | None:
        sheet = load_image(ARROW_SHEET)
        if sheet is None:
            return None

        import pygame

        frame_width = min(sheet.get_width(), max(1, sheet.get_height()))
        rect = pygame.Rect(0, 0, frame_width, sheet.get_height())
        if not sheet.get_rect().contains(rect):
            return None
        frame = sheet.subsurface(rect).copy()
        return pygame.transform.smoothscale(frame, (18, 18))
