from __future__ import annotations

from math import atan2, degrees
from pathlib import Path
from typing import Any

from shared.asset_manifest import (
    ARROW_SHEET,
    FIREBALL_SHEET,
    TOWER_IDLE_ASSETS,
    TOWER_IDLE_FALLBACK_ASSETS,
    TOWER_UNIT_SHEETS,
)
from shared.contracts import TowerKind
from shared.assets import load_image
from towers.models import Facing, Projectile, TowerRuntime


_BASE_FRAME_WIDTH = 70
_BASE_FRAME_HEIGHT = 130
_UNIT_FRAME_SIZE = 48
_ARROW_RENDER_HEIGHT = 22
_FIREBALL_RENDER_SIZE = 24
_MAGE_UNIT_RENDER_SIZE = 40
_ARROW_SOURCE_OFFSET = -90.0
_FIREBALL_SOURCE_OFFSET = -90.0

# BuildRequest.position is the centre of the build cell. The base PNG has a
# low anchor. Each tower artwork has its platform at a different height, so the
# archer must use an individual platform anchor for every tower type.
#
# These values are measured from the lower anchor of the tower base upward.
# Values are measured per base sheet, so every upgrade level has its own anchor.
_BASE_BOTTOM_OFFSET_Y = 32
_UNIT_PLATFORM_RISE_FROM_BASE_BOTTOM: dict[TowerKind, int] = {
    TowerKind.ARCHER_1: 30,
    TowerKind.ARCHER_2: 40,
    TowerKind.ARCHER_3: 50,
    TowerKind.ARCHER_4: 48,
    TowerKind.ARCHER_5: 52,
    TowerKind.ARCHER_6: 57,
    TowerKind.ARCHER_7: 55,
    TowerKind.ARCHER_8: 55,
    TowerKind.MAGE_1: 34,
    TowerKind.MAGE_2: 38,
    TowerKind.MAGE_3: 44,
    TowerKind.MAGE_4: 48,
    TowerKind.MAGE_5: 52,
    TowerKind.MAGE_6: 60,
    TowerKind.MAGE_7: 66,
    TowerKind.MAGE_8: 66,
}
_DEFAULT_UNIT_PLATFORM_RISE = 48

# The supplied asset pack has up_*.png, down_*.png and side_*.png only.
# Its side animation faces left; facing right is the same image mirrored.
_SIDE_SPRITE_FACING = Facing.LEFT


class TowerRenderer:
    """Рисует PNG-кадры башен, лучников и стрел без масштабирования sheet целиком."""

    def __init__(self) -> None:
        self._base_frames: dict[tuple[object, int], Any] = {}
        self._unit_frames: dict[tuple[object, Facing, bool, bool, int], Any] = {}
        self._arrow_frame: Any | None = None
        self._arrow_was_loaded = False
        self._fireball_frame: Any | None = None
        self._fireball_was_loaded = False

    def draw_tower(self, surface: Any, tower: TowerRuntime) -> None:
        x = int(tower.request.position.x)
        y = int(tower.request.position.y)
        base_bottom_y = y + _BASE_BOTTOM_OFFSET_Y

        base_frame = self._load_base_frame(tower)
        if base_frame is not None:
            base_rect = base_frame.get_rect(midbottom=(x, base_bottom_y))
            surface.blit(base_frame, base_rect)

        unit_frame = self._load_unit_frame(tower)
        if unit_frame is not None:
            platform_rise = _UNIT_PLATFORM_RISE_FROM_BASE_BOTTOM.get(
                tower.kind,
                _DEFAULT_UNIT_PLATFORM_RISE,
            )
            unit_bottom_y = base_bottom_y - platform_rise
            unit_rect = unit_frame.get_rect(midbottom=(x, unit_bottom_y))
            surface.blit(unit_frame, unit_rect)

        self._draw_level_badge(surface, tower.level, x + 25, y - 35)

    def draw_projectile(self, surface: Any, projectile: Projectile) -> None:
        import pygame

        x = int(projectile.position.x)
        y = int(projectile.position.y)
        if projectile.projectile_kind == "fireball":
            fireball = self._load_fireball_frame()
            if fireball is not None:
                angle = (
                    -degrees(atan2(projectile.direction.y, projectile.direction.x))
                    + _FIREBALL_SOURCE_OFFSET
                )
                rotated = pygame.transform.rotate(fireball, angle)
                surface.blit(rotated, rotated.get_rect(center=(x, y)))
                return

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
        line_color = (91, 213, 255) if projectile.projectile_kind == "fireball" else (244, 218, 130)
        pygame.draw.line(surface, line_color, (x, y), (end_x, end_y), 2)

    def _load_base_frame(self, tower: TowerRuntime) -> Any | None:
        sheet = self._load_base_sheet(tower.kind)
        if sheet is None:
            return None

        frame_count = max(1, sheet.get_width() // _BASE_FRAME_WIDTH)
        frame_index = (
            int(tower.animation_time * 5) % frame_count
            if tower.attack_animation_remaining > 0.0
            else 0
        )
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

    @staticmethod
    def _load_base_sheet(kind: TowerKind) -> Any | None:
        """Loads a level's base sheet with a visual fallback for level VIII.

        The current asset archive includes archer_1.png through archer_7.png.
        When archer_8.png is later added, it will be used automatically. Until
        then level VIII keeps working and displays the final available model.
        """
        sheet = load_image(TOWER_IDLE_ASSETS[kind])
        if sheet is not None:
            return sheet

        fallback = TOWER_IDLE_FALLBACK_ASSETS.get(kind)
        return None if fallback is None else load_image(fallback)

    def _load_unit_frame(self, tower: TowerRuntime) -> Any | None:
        sheet, is_attacking, flip_x = self._load_unit_sheet(tower)
        if sheet is None:
            return None

        frame_count = max(1, sheet.get_width() // _UNIT_FRAME_SIZE)
        frames_per_second = 12 if is_attacking else 6
        frame_index = (
            int(tower.animation_time * frames_per_second) % frame_count
            if is_attacking
            else 0
        )
        cache_key = (tower.kind, tower.facing, is_attacking, flip_x, frame_index)
        cached = self._unit_frames.get(cache_key)
        if cached is not None:
            return cached

        frame = self._frame_from_sheet(
            sheet,
            frame_width=_UNIT_FRAME_SIZE,
            frame_height=_UNIT_FRAME_SIZE,
            frame_index=frame_index,
        )
        if frame is None:
            return None

        if flip_x:
            import pygame

            frame = pygame.transform.flip(frame, True, False)

        frame = self._trim_unit_bottom_padding(frame)
        frame = self._scale_unit_frame_for_kind(tower.kind, frame)
        self._unit_frames[cache_key] = frame
        return frame

    def _load_unit_sheet(self, tower: TowerRuntime) -> tuple[Any | None, bool, bool]:
        idle_path = TOWER_UNIT_SHEETS[tower.kind]
        requested_state = "attack" if tower.attack_animation_remaining > 0.0 else "idle"

        for path, is_attacking, flip_x in self._unit_sheet_candidates(
            idle_path,
            tower.facing,
            requested_state,
        ):
            sheet = load_image(path)
            if sheet is not None:
                return sheet, is_attacking, flip_x

        return None, False, False

    @staticmethod
    def _unit_sheet_candidates(
        idle_path: Path,
        facing: Facing,
        requested_state: str,
    ) -> tuple[tuple[Path, bool, bool], ...]:
        """Returns existing-pack filenames in the right visual direction.

        The pack provides only a single ``side_*.png`` sheet. That sheet faces
        left, so it is used directly for ``Facing.LEFT`` and mirrored only for
        ``Facing.RIGHT``. No attempt is made to load nonexistent left/right
        files, which was the reason horizontal turns previously fell back to
        the down-facing sprite.
        """
        asset_direction, flip_x = TowerRenderer._asset_direction_for(idle_path, facing)
        states = TowerRenderer._state_candidates(requested_state)

        candidates: list[tuple[Path, bool, bool]] = []
        seen: set[tuple[Path, bool]] = set()

        def add(direction: str, state: str, *, mirrored: bool) -> None:
            path = idle_path.with_name(f"{direction}_{state}.png")
            is_attacking = state in {"attack", "preattack"}
            key = (path, mirrored)
            if key not in seen:
                seen.add(key)
                candidates.append((path, is_attacking, mirrored))

        for state in states:
            add(asset_direction, state, mirrored=flip_x)

        # A partial asset import should still render a unit rather than hide it.
        if asset_direction != "down":
            for state in states:
                add("down", state, mirrored=False)

        return tuple(candidates)

    @staticmethod
    def _asset_direction_for(idle_path: Path, facing: Facing) -> tuple[str, bool]:
        if facing == Facing.UP:
            return "up", False
        if facing == Facing.DOWN:
            return "down", False

        unit_folder = idle_path.parent.name
        if unit_folder.startswith("mage_"):
            return facing.value, False

        if facing == _SIDE_SPRITE_FACING:
            return "side", False
        return "side", True

    @staticmethod
    def _state_candidates(requested_state: str) -> tuple[str, ...]:
        if requested_state == "attack":
            return "attack", "preattack", "idle"
        return "idle",

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


    @staticmethod
    def _scale_unit_frame_for_kind(kind: TowerKind, frame: Any) -> Any:
        if not kind.value.startswith("mage_"):
            return frame

        width, height = frame.get_size()
        if width <= 0 or height <= 0:
            return frame

        scale = min(
            _MAGE_UNIT_RENDER_SIZE / width,
            _MAGE_UNIT_RENDER_SIZE / height,
            1.0,
        )
        target_size = (
            max(1, round(width * scale)),
            max(1, round(height * scale)),
        )
        if target_size == (width, height):
            return frame

        import pygame

        return pygame.transform.scale(frame, target_size)

    @staticmethod
    def _trim_unit_bottom_padding(frame: Any) -> Any:
        """Removes only transparent rows below the archer's feet.

        Sprite sheets in this pack use a 48×48 frame but the actual person is
        shorter. Anchoring the full transparent rectangle makes the visible
        archer float above the tower. The trim preserves the frame width and
        top edge, so animation frames do not jump sideways.
        """
        get_bounding_rect = getattr(frame, "get_bounding_rect", None)
        if not callable(get_bounding_rect):
            return frame

        try:
            visible = get_bounding_rect(min_alpha=1)
        except TypeError:
            try:
                visible = get_bounding_rect()
            except (AttributeError, TypeError, ValueError):
                return frame
        except (AttributeError, TypeError, ValueError):
            return frame

        if visible is None:
            return frame

        width, height = frame.get_size()
        visible_bottom = getattr(
            visible,
            "bottom",
            getattr(visible, "y", 0) + getattr(visible, "height", 0),
        )
        if visible_bottom <= 0 or visible_bottom >= height:
            return frame

        import pygame

        return frame.subsurface(pygame.Rect(0, 0, width, visible_bottom)).copy()

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

        # arrow_1.png is an individual 3x14 arrow, not a sprite sheet.
        # Scaling it proportionally keeps the pixel-art silhouette narrow.
        self._arrow_frame = pygame.transform.scale(
            arrow,
            (target_width, target_height),
        )
        return self._arrow_frame

    def _load_fireball_frame(self) -> Any | None:
        if self._fireball_was_loaded:
            return self._fireball_frame

        self._fireball_was_loaded = True
        fireball = load_image(FIREBALL_SHEET)
        if fireball is None:
            return None

        width, height = fireball.get_size()
        if width <= 0 or height <= 0:
            return None

        import pygame

        self._fireball_frame = pygame.transform.scale(
            fireball,
            (_FIREBALL_RENDER_SIZE, _FIREBALL_RENDER_SIZE),
        )
        return self._fireball_frame

    @staticmethod
    def _draw_level_badge(surface: Any, level: int, x: int, y: int) -> None:
        import pygame

        badge = pygame.font.Font(None, 19).render(str(level), True, (255, 248, 205))
        badge_rect = badge.get_rect(center=(x, y))
        background = badge_rect.inflate(7, 5)
        pygame.draw.rect(surface, (43, 45, 58), background, border_radius=4)
        surface.blit(badge, badge_rect)
