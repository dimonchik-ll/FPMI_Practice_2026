from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import hypot

import pygame

from shared.contracts import (
    GameSnapshot,
    TOWER_DEFINITIONS,
    TowerView,
    UiAction,
    UiActionKind,
    next_tower_kind,
)
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import draw_centered_text, draw_text, wrap_text


class _DialogKind(str, Enum):
    UPGRADE = "upgrade"
    REMOVE = "remove"


class _ActionButton(str, Enum):
    UPGRADE = "upgrade"
    DELETE = "delete"


@dataclass(frozen=True, slots=True)
class _ButtonStyle:
    fill: Color
    border: Color
    text: Color


class TowerActionMenu:
    """Compact animated action menu displayed below a tower after right-click."""

    _BUTTON_RADIUS = 20
    _HOVER_RADIUS_BONUS = 4
    _PRESSED_RADIUS_BONUS = -2
    _BUTTON_GAP = 10
    _BUTTON_Y_OFFSET = 42
    _MAP_MARGIN = 10
    _SHADOW_OFFSET = 3
    _ANIMATION_SPEED = 14.0
    _RANGE_FILL: Color = (115, 208, 255, 28)
    _RANGE_BORDER: Color = (151, 226, 255, 145)
    _RANGE_DIALOG_FILL: Color = (115, 208, 255, 20)
    _RANGE_DIALOG_BORDER: Color = (151, 226, 255, 112)
    _RANGE_BORDER_WIDTH = 2

    _DIALOG_WIDTH = 440
    _DIALOG_MIN_HEIGHT = 306
    _DIALOG_PADDING = 18
    _DIALOG_BUTTON_WIDTH = 136
    _DIALOG_BUTTON_HEIGHT = 40
    _DIALOG_BUTTON_GAP = 14
    _DIALOG_BOTTOM_GAP = 18
    _DIALOG_SIDE_MARGIN = 28
    _VALUE_ROW_HEIGHT = 28
    _STAT_ROW_HEIGHT = 28
    _STAT_ROW_GAP = 6

    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts
        self._tower_id: str | None = None
        self._dialog_kind: _DialogKind | None = None
        self._hovered_button: _ActionButton | None = None
        self._pressed_button: _ActionButton | None = None
        self._animation_progress: dict[_ActionButton, float] = {
            _ActionButton.UPGRADE: 0.0,
            _ActionButton.DELETE: 0.0,
        }
        self._last_animation_tick = pygame.time.get_ticks()

    @property
    def is_open(self) -> bool:
        return self._tower_id is not None

    def open(self, tower_identifier: str) -> None:
        self._tower_id = tower_identifier
        self._dialog_kind = None
        self._hovered_button = None
        self._pressed_button = None
        for button in self._animation_progress:
            self._animation_progress[button] = 0.0
        self._last_animation_tick = pygame.time.get_ticks()

    def close(self) -> None:
        self._tower_id = None
        self._dialog_kind = None
        self._hovered_button = None
        self._pressed_button = None

    def sync(self, snapshot: GameSnapshot) -> None:
        if self._tower_id is None:
            return

        if self._selected_tower(snapshot) is None:
            self.close()

    def contains_point(self, position: tuple[int, int]) -> bool:
        return self.is_open

    def handle_event(
        self,
        event: pygame.event.Event,
        snapshot: GameSnapshot,
    ) -> UiAction | None:
        self.sync(snapshot)
        tower = self._selected_tower(snapshot)

        if tower is None:
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._dialog_kind is not None:
                self._dialog_kind = None
                return None

            return UiAction(UiActionKind.CLOSE_TOWER_MENU)

        if self._dialog_kind is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self._handle_dialog_click(event.pos, tower, snapshot)
            return None

        if event.type == pygame.MOUSEMOTION:
            self._hovered_button = self._button_at_position(tower, event.pos)
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_button = self._button_at_position(tower, event.pos)
            if clicked_button is None:
                return UiAction(UiActionKind.CLOSE_TOWER_MENU)

            self._pressed_button = clicked_button
            self._hovered_button = clicked_button
            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            released_button = self._button_at_position(tower, event.pos)
            pressed_button = self._pressed_button
            self._pressed_button = None

            if pressed_button is None:
                return None

            if released_button != pressed_button:
                return None

            if pressed_button == _ActionButton.UPGRADE:
                if tower.can_upgrade:
                    self._dialog_kind = _DialogKind.UPGRADE
                return None

            if pressed_button == _ActionButton.DELETE:
                self._dialog_kind = _DialogKind.REMOVE
                return None

        return None

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self.sync(snapshot)
        tower = self._selected_tower(snapshot)

        if tower is None:
            return

        if self._dialog_kind is not None:
            self._draw_map_shade(surface)
            self._draw_attack_range(surface, tower, dimmed=True)
            self._draw_radial_buttons(surface, tower, snapshot, dimmed=True)
            self._draw_confirmation_dialog(surface, tower, snapshot)
            return

        self._draw_attack_range(surface, tower, dimmed=False)
        self._hovered_button = self._button_at_position(tower, pygame.mouse.get_pos())
        self._update_animation()
        self._draw_radial_buttons(surface, tower, snapshot, dimmed=False)

    def _draw_attack_range(
        self,
        surface: pygame.Surface,
        tower: TowerView,
        *,
        dimmed: bool,
    ) -> None:
        radius = int(round(tower.attack_range))

        if radius <= 0:
            return

        map_width = max(1, min(self._layout.map_width, surface.get_width()))
        map_height = max(1, min(self._layout.height, surface.get_height()))
        overlay = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        center = (round(tower.position.x), round(tower.position.y))
        fill = self._RANGE_DIALOG_FILL if dimmed else self._RANGE_FILL
        border = self._RANGE_DIALOG_BORDER if dimmed else self._RANGE_BORDER

        pygame.draw.circle(overlay, fill, center, radius)
        pygame.draw.circle(
            overlay,
            border,
            center,
            radius,
            width=self._RANGE_BORDER_WIDTH,
        )
        pygame.draw.circle(
            overlay,
            border,
            center,
            3,
        )
        surface.blit(overlay, (0, 0))

    def _handle_dialog_click(
        self,
        position: tuple[int, int],
        tower: TowerView,
        snapshot: GameSnapshot,
    ) -> UiAction | None:
        if self._dialog_cancel_rect(tower, snapshot).collidepoint(position):
            self._dialog_kind = None
            return None

        if not self._dialog_ok_rect(tower, snapshot).collidepoint(position):
            return None

        dialog_kind = self._dialog_kind
        self._dialog_kind = None

        if dialog_kind == _DialogKind.UPGRADE:
            if self._can_upgrade(tower, snapshot):
                return UiAction(
                    UiActionKind.UPGRADE_TOWER,
                    {"tower_id": tower.identifier},
                )

            return None

        if dialog_kind == _DialogKind.REMOVE:
            return UiAction(
                UiActionKind.REMOVE_TOWER,
                {"tower_id": tower.identifier},
            )

        return None

    def _draw_radial_buttons(
        self,
        surface: pygame.Surface,
        tower: TowerView,
        snapshot: GameSnapshot,
        *,
        dimmed: bool,
    ) -> None:
        upgrade_center, delete_center = self._button_centers(tower)

        self._draw_circle_button(
            surface,
            upgrade_center,
            self._upgrade_button_style(tower, snapshot, dimmed=dimmed),
            icon="upgrade",
            action_button=_ActionButton.UPGRADE,
            disabled=not tower.can_upgrade,
            dimmed=dimmed,
        )
        self._draw_circle_button(
            surface,
            delete_center,
            self._delete_button_style(dimmed=dimmed),
            icon="delete",
            action_button=_ActionButton.DELETE,
            disabled=False,
            dimmed=dimmed,
        )

    def _draw_circle_button(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        style: _ButtonStyle,
        *,
        icon: str,
        action_button: _ActionButton,
        disabled: bool,
        dimmed: bool,
    ) -> None:
        progress = 0.0 if dimmed else self._animation_progress[action_button]
        radius = self._animated_radius(action_button, progress, dimmed=dimmed)
        center = self._animated_center(center, action_button)

        shadow_alpha = 92 if dimmed else 126 + int(progress * 42)
        shadow_radius = radius + 2 + int(progress * 2)
        shadow = pygame.Surface((shadow_radius * 2 + 8, shadow_radius * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(
            shadow,
            (0, 0, 0, shadow_alpha),
            (shadow.get_width() // 2 + self._SHADOW_OFFSET, shadow.get_height() // 2 + self._SHADOW_OFFSET),
            shadow_radius,
        )
        surface.blit(
            shadow,
            (center[0] - shadow.get_width() // 2, center[1] - shadow.get_height() // 2),
        )

        if progress > 0.03 and not dimmed:
            glow_radius = radius + 5
            glow = pygame.Surface((glow_radius * 2 + 4, glow_radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(
                glow,
                (*style.border, int(38 + progress * 58)),
                (glow.get_width() // 2, glow.get_height() // 2),
                glow_radius,
                width=2,
            )
            surface.blit(
                glow,
                (center[0] - glow.get_width() // 2, center[1] - glow.get_height() // 2),
            )

        pygame.draw.circle(surface, style.fill, center, radius)
        pygame.draw.circle(surface, style.border, center, radius, width=3 if progress > 0.35 else 2)

        if icon == "upgrade":
            self._draw_upgrade_icon(surface, center, style.text, disabled=disabled, scale=radius / self._BUTTON_RADIUS)
        else:
            self._draw_delete_icon(surface, center, style.text, scale=radius / self._BUTTON_RADIUS)

    def _draw_upgrade_icon(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        color: Color,
        *,
        disabled: bool,
        scale: float,
    ) -> None:
        x, y = center
        arrow_color = self._theme.muted_text if disabled else color
        height = max(8, int(11 * scale))
        half = max(6, int(8 * scale))
        stem_half = max(2, int(3 * scale))

        pygame.draw.polygon(
            surface,
            arrow_color,
            (
                (x, y - height),
                (x - half, y - 1),
                (x - stem_half, y - 1),
                (x - stem_half, y + height),
                (x + stem_half, y + height),
                (x + stem_half, y - 1),
                (x + half, y - 1),
            ),
        )

    def _draw_delete_icon(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        color: Color,
        *,
        scale: float,
    ) -> None:
        x, y = center
        body_width = max(11, int(14 * scale))
        body_height = max(12, int(15 * scale))
        body = pygame.Rect(0, 0, body_width, body_height)
        body.center = (x, y + int(3 * scale))
        lid = pygame.Rect(0, 0, body_width + 4, max(3, int(3 * scale)))
        lid.center = (x, y - int(7 * scale))

        line_width = max(1, int(2 * scale))
        pygame.draw.rect(surface, color, lid, border_radius=1)
        pygame.draw.line(
            surface,
            color,
            (x - int(4 * scale), lid.y - int(3 * scale)),
            (x + int(4 * scale), lid.y - int(3 * scale)),
            max(2, line_width),
        )
        pygame.draw.rect(surface, color, body, width=line_width, border_radius=2)
        pygame.draw.line(surface, color, (x - int(3 * scale), body.y + 4), (x - int(3 * scale), body.bottom - 4), line_width)
        pygame.draw.line(surface, color, (x + int(3 * scale), body.y + 4), (x + int(3 * scale), body.bottom - 4), line_width)

    def _draw_confirmation_dialog(
        self,
        surface: pygame.Surface,
        tower: TowerView,
        snapshot: GameSnapshot,
    ) -> None:
        dialog = self._dialog_rect(tower, snapshot)

        pygame.draw.rect(
            surface,
            self._theme.panel_background,
            dialog,
            border_radius=14,
        )
        pygame.draw.rect(
            surface,
            self._theme.panel_border,
            dialog,
            width=2,
            border_radius=14,
        )

        y = dialog.y + self._DIALOG_PADDING
        title = (
            "Удалить башню?"
            if self._dialog_kind == _DialogKind.REMOVE
            else "Подтвердить улучшение"
        )

        draw_text(
            surface,
            title,
            self._fonts.section,
            self._theme.title_text,
            (dialog.x + self._DIALOG_PADDING, y),
        )
        y += self._fonts.section.get_linesize() + 10

        if self._dialog_kind == _DialogKind.REMOVE:
            self._draw_remove_dialog_body(surface, dialog, tower, y)
        else:
            self._draw_upgrade_dialog_body(surface, dialog, tower, snapshot, y)

        self._draw_dialog_button(
            surface,
            self._dialog_cancel_rect(tower, snapshot),
            "ОТМЕНА",
            _ButtonStyle(
                fill=self._theme.default_card,
                border=self._theme.default_card_border,
                text=self._theme.body_text,
            ),
        )
        self._draw_dialog_button(
            surface,
            self._dialog_ok_rect(tower, snapshot),
            "ОК",
            _ButtonStyle(
                fill=self._ok_button_fill(tower, snapshot),
                border=self._ok_button_border(tower, snapshot),
                text=self._ok_button_text_color(tower, snapshot),
            ),
        )

    def _draw_remove_dialog_body(
        self,
        surface: pygame.Surface,
        dialog: pygame.Rect,
        tower: TowerView,
        y: int,
    ) -> None:
        text_width = dialog.width - self._DIALOG_PADDING * 2
        description = (
            f"Башня {TOWER_DEFINITIONS[tower.kind].title} будет удалена, "
            "а клетка строительства снова станет свободной."
        )

        for line in wrap_text(description, self._fonts.small, text_width):
            draw_text(
                surface,
                line,
                self._fonts.small,
                self._theme.body_text,
                (dialog.x + self._DIALOG_PADDING, y),
            )
            y += self._fonts.small.get_linesize()

        y += 12
        self._draw_value_row(
            surface,
            dialog,
            y,
            "Возврат монет",
            "0",
            value_color=(235, 202, 118),
        )

    def _draw_upgrade_dialog_body(
        self,
        surface: pygame.Surface,
        dialog: pygame.Rect,
        tower: TowerView,
        snapshot: GameSnapshot,
        y: int,
    ) -> None:
        next_kind = next_tower_kind(tower.kind)

        if next_kind is None:
            draw_text(
                surface,
                "Эта башня уже находится на максимальном уровне.",
                self._fonts.small,
                self._theme.body_text,
                (dialog.x + self._DIALOG_PADDING, y),
            )
            return

        current = TOWER_DEFINITIONS[tower.kind]
        upgraded = TOWER_DEFINITIONS[next_kind]
        cost = tower.upgrade_cost or 0
        missing_money = max(0, cost - snapshot.player.money)

        draw_text(
            surface,
            f"{current.title} → {upgraded.title}",
            self._fonts.small,
            self._theme.body_text,
            (dialog.x + self._DIALOG_PADDING, y),
        )
        y += self._fonts.small.get_linesize() + 8

        self._draw_value_row(
            surface,
            dialog,
            y,
            "Стоимость",
            f"{cost} мон.",
            value_color=(235, 202, 118),
        )
        y += self._VALUE_ROW_HEIGHT + 8

        if missing_money > 0:
            self._draw_value_row(
                surface,
                dialog,
                y,
                "Не хватает",
                f"{missing_money} мон.",
                value_color=(236, 138, 113),
            )
            y += self._VALUE_ROW_HEIGHT + 8

        draw_text(
            surface,
            "ИЗМЕНЯЕМЫЕ ХАРАКТЕРИСТИКИ",
            self._fonts.small,
            self._theme.muted_text,
            (dialog.x + self._DIALOG_PADDING, y),
        )
        y += self._fonts.small.get_linesize() + 6

        for label, old_value, new_value, improved in (
            ("Урон", str(current.damage), str(upgraded.damage), upgraded.damage >= current.damage),
            (
                "Дальность",
                str(int(current.attack_range)),
                str(int(upgraded.attack_range)),
                upgraded.attack_range >= current.attack_range,
            ),
            (
                "Скорость атаки",
                f"{current.attacks_per_second:.1f}/с",
                f"{upgraded.attacks_per_second:.1f}/с",
                upgraded.attacks_per_second >= current.attacks_per_second,
            ),
        ):
            self._draw_stat_change_row(
                surface,
                dialog,
                y,
                label,
                old_value,
                new_value,
                improved=improved,
            )
            y += self._STAT_ROW_HEIGHT + self._STAT_ROW_GAP

    def _draw_value_row(
        self,
        surface: pygame.Surface,
        dialog: pygame.Rect,
        y: int,
        label: str,
        value: str,
        *,
        value_color: Color,
    ) -> None:
        row = pygame.Rect(
            dialog.x + self._DIALOG_PADDING,
            y,
            dialog.width - self._DIALOG_PADDING * 2,
            self._VALUE_ROW_HEIGHT,
        )
        pygame.draw.rect(surface, self._theme.default_card, row, border_radius=6)
        pygame.draw.rect(surface, self._theme.default_card_border, row, width=1, border_radius=6)

        draw_text(
            surface,
            label,
            self._fonts.small,
            self._theme.muted_text,
            (row.x + 10, row.centery - self._fonts.small.get_height() // 2),
        )
        value_surface = self._fonts.small.render(value, True, value_color)
        surface.blit(value_surface, (row.right - 10 - value_surface.get_width(), row.centery - value_surface.get_height() // 2))

    def _draw_stat_change_row(
        self,
        surface: pygame.Surface,
        dialog: pygame.Rect,
        y: int,
        label: str,
        old_value: str,
        new_value: str,
        *,
        improved: bool,
    ) -> None:
        row = pygame.Rect(
            dialog.x + self._DIALOG_PADDING,
            y,
            dialog.width - self._DIALOG_PADDING * 2,
            self._STAT_ROW_HEIGHT,
        )

        label_x = row.x + 10
        old_x = row.right - 148
        arrow_x = row.right - 90
        new_x = row.right - 56
        new_color: Color = (151, 204, 134) if improved else (236, 138, 113)

        draw_text(
            surface,
            label,
            self._fonts.small,
            self._theme.body_text,
            (label_x, row.y + 2),
        )
        draw_text(
            surface,
            old_value,
            self._fonts.small,
            self._theme.muted_text,
            (old_x, row.y + 2),
        )
        draw_text(
            surface,
            "→",
            self._fonts.small,
            self._theme.muted_text,
            (arrow_x, row.y + 2),
        )
        draw_text(
            surface,
            new_value,
            self._fonts.small,
            new_color,
            (new_x, row.y + 2),
        )

    def _draw_map_shade(self, surface: pygame.Surface) -> None:
        map_area = pygame.Rect(0, 0, self._layout.map_width, self._layout.height)
        shade = pygame.Surface(map_area.size, pygame.SRCALPHA)
        shade.fill((8, 13, 19, 138))
        surface.blit(shade, map_area.topleft)

    def _draw_dialog_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        style: _ButtonStyle,
    ) -> None:
        pygame.draw.rect(surface, style.fill, rect, border_radius=8)
        pygame.draw.rect(surface, style.border, rect, width=2, border_radius=8)
        draw_centered_text(
            surface,
            label,
            self._fonts.small,
            style.text,
            rect,
        )

    def _selected_tower(self, snapshot: GameSnapshot) -> TowerView | None:
        if self._tower_id is None:
            return None

        return next(
            (tower for tower in snapshot.towers if tower.identifier == self._tower_id),
            None,
        )

    def _button_centers(self, tower: TowerView) -> tuple[tuple[int, int], tuple[int, int]]:
        radius = self._BUTTON_RADIUS + self._HOVER_RADIUS_BONUS
        map_rect = pygame.Rect(0, 0, self._layout.map_width, self._layout.height)

        left_x = int(tower.position.x - self._BUTTON_RADIUS - self._BUTTON_GAP // 2)
        right_x = int(tower.position.x + self._BUTTON_RADIUS + self._BUTTON_GAP // 2)
        center_y = int(tower.position.y + self._BUTTON_Y_OFFSET)

        if center_y + radius > map_rect.bottom - self._MAP_MARGIN:
            center_y = int(tower.position.y - self._BUTTON_Y_OFFSET)

        min_x = map_rect.left + self._MAP_MARGIN + radius
        max_x = map_rect.right - self._MAP_MARGIN - radius

        if left_x < min_x:
            shift = min_x - left_x
            left_x += shift
            right_x += shift

        if right_x > max_x:
            shift = right_x - max_x
            left_x -= shift
            right_x -= shift

        center_y = max(
            map_rect.top + self._MAP_MARGIN + radius,
            min(center_y, map_rect.bottom - self._MAP_MARGIN - radius),
        )

        return (left_x, center_y), (right_x, center_y)

    def _dialog_rect(self, tower: TowerView, snapshot: GameSnapshot) -> pygame.Rect:
        width = min(
            self._DIALOG_WIDTH,
            max(300, self._layout.map_width - self._DIALOG_SIDE_MARGIN * 2),
        )
        content_width = width - self._DIALOG_PADDING * 2
        body_height = self._dialog_body_height(tower, snapshot, content_width)
        title_height = self._fonts.section.get_linesize()
        content_height = (
            self._DIALOG_PADDING
            + title_height
            + 10
            + body_height
            + self._DIALOG_BOTTOM_GAP
            + self._DIALOG_BUTTON_HEIGHT
            + self._DIALOG_PADDING
        )
        available_height = max(220, self._layout.height - self._DIALOG_SIDE_MARGIN * 2)
        height = min(
            available_height,
            max(self._DIALOG_MIN_HEIGHT, content_height),
        )

        return pygame.Rect(
            (self._layout.map_width - width) // 2,
            (self._layout.height - height) // 2,
            width,
            height,
        )

    def _dialog_body_height(
        self,
        tower: TowerView,
        snapshot: GameSnapshot,
        content_width: int,
    ) -> int:
        if self._dialog_kind == _DialogKind.REMOVE:
            description = (
                f"Башня {TOWER_DEFINITIONS[tower.kind].title} будет удалена, "
                "а клетка строительства снова станет свободной."
            )
            line_count = max(1, len(wrap_text(description, self._fonts.small, content_width)))
            return (
                line_count * self._fonts.small.get_linesize()
                + 12
                + self._VALUE_ROW_HEIGHT
            )

        next_kind = next_tower_kind(tower.kind)
        if next_kind is None:
            text = "Эта башня уже находится на максимальном уровне."
            line_count = max(1, len(wrap_text(text, self._fonts.small, content_width)))
            return line_count * self._fonts.small.get_linesize()

        cost = tower.upgrade_cost or 0
        missing_money = max(0, cost - snapshot.player.money)
        stat_count = 3
        return (
            self._fonts.small.get_linesize()
            + 8
            + self._VALUE_ROW_HEIGHT
            + 8
            + (self._VALUE_ROW_HEIGHT + 8 if missing_money > 0 else 0)
            + self._fonts.small.get_linesize()
            + 6
            + stat_count * self._STAT_ROW_HEIGHT
            + (stat_count - 1) * self._STAT_ROW_GAP
        )

    def _dialog_cancel_rect(
        self,
        tower: TowerView,
        snapshot: GameSnapshot,
    ) -> pygame.Rect:
        dialog = self._dialog_rect(tower, snapshot)
        total_width = self._DIALOG_BUTTON_WIDTH * 2 + self._DIALOG_BUTTON_GAP
        x = dialog.centerx - total_width // 2
        y = dialog.bottom - self._DIALOG_PADDING - self._DIALOG_BUTTON_HEIGHT
        return pygame.Rect(x, y, self._DIALOG_BUTTON_WIDTH, self._DIALOG_BUTTON_HEIGHT)

    def _dialog_ok_rect(
        self,
        tower: TowerView,
        snapshot: GameSnapshot,
    ) -> pygame.Rect:
        cancel = self._dialog_cancel_rect(tower, snapshot)
        return pygame.Rect(
            cancel.right + self._DIALOG_BUTTON_GAP,
            cancel.y,
            self._DIALOG_BUTTON_WIDTH,
            self._DIALOG_BUTTON_HEIGHT,
        )

    def _can_upgrade(self, tower: TowerView, snapshot: GameSnapshot) -> bool:
        return tower.can_upgrade and snapshot.player.money >= (tower.upgrade_cost or 0)

    def _button_at_position(
        self,
        tower: TowerView,
        position: tuple[int, int],
    ) -> _ActionButton | None:
        upgrade_center, delete_center = self._button_centers(tower)

        if self._circle_contains(upgrade_center, position):
            return _ActionButton.UPGRADE

        if self._circle_contains(delete_center, position):
            return _ActionButton.DELETE

        return None

    def _update_animation(self) -> None:
        current_tick = pygame.time.get_ticks()
        delta_seconds = max(0.0, min(0.05, (current_tick - self._last_animation_tick) / 1000.0))
        self._last_animation_tick = current_tick

        step = min(1.0, delta_seconds * self._ANIMATION_SPEED)
        for button in self._animation_progress:
            target = 1.0 if self._hovered_button == button else 0.0
            value = self._animation_progress[button]
            self._animation_progress[button] = value + (target - value) * step

    def _animated_radius(
        self,
        action_button: _ActionButton,
        progress: float,
        *,
        dimmed: bool,
    ) -> int:
        radius = self._BUTTON_RADIUS

        if not dimmed:
            radius += int(round(self._HOVER_RADIUS_BONUS * progress))

        if self._pressed_button == action_button:
            radius += self._PRESSED_RADIUS_BONUS

        return max(15, radius)

    def _animated_center(
        self,
        center: tuple[int, int],
        action_button: _ActionButton,
    ) -> tuple[int, int]:
        if self._pressed_button == action_button:
            return (center[0], center[1] + 1)

        return center

    def _upgrade_button_style(
        self,
        tower: TowerView,
        snapshot: GameSnapshot,
        *,
        dimmed: bool,
    ) -> _ButtonStyle:
        if dimmed:
            return _ButtonStyle(
                fill=self._theme.unavailable_card,
                border=self._theme.unavailable_card_border,
                text=self._theme.muted_text,
            )

        if self._can_upgrade(tower, snapshot):
            return _ButtonStyle(
                fill=self._theme.selected_card,
                border=self._theme.selected_card_border,
                text=self._theme.body_text,
            )

        if tower.can_upgrade:
            return _ButtonStyle(
                fill=self._theme.unavailable_card,
                border=(171, 134, 66),
                text=(235, 202, 118),
            )

        return _ButtonStyle(
            fill=self._theme.unavailable_card,
            border=self._theme.unavailable_card_border,
            text=self._theme.muted_text,
        )

    def _delete_button_style(self, *, dimmed: bool) -> _ButtonStyle:
        if dimmed:
            return _ButtonStyle(
                fill=(71, 45, 49),
                border=(116, 74, 78),
                text=self._theme.muted_text,
            )

        return _ButtonStyle(
            fill=(116, 58, 57),
            border=(223, 137, 128),
            text=self._theme.body_text,
        )

    def _ok_button_fill(self, tower: TowerView, snapshot: GameSnapshot) -> Color:
        if self._dialog_kind == _DialogKind.REMOVE:
            return (116, 58, 57)

        if not self._can_upgrade(tower, snapshot):
            return self._theme.unavailable_card

        return self._theme.selected_card

    def _ok_button_border(self, tower: TowerView, snapshot: GameSnapshot) -> Color:
        if self._dialog_kind == _DialogKind.REMOVE:
            return (223, 137, 128)

        if not self._can_upgrade(tower, snapshot):
            return self._theme.unavailable_card_border

        return self._theme.selected_card_border

    def _ok_button_text_color(self, tower: TowerView, snapshot: GameSnapshot) -> Color:
        if self._dialog_kind == _DialogKind.UPGRADE and not self._can_upgrade(tower, snapshot):
            return self._theme.muted_text

        return self._theme.body_text

    @staticmethod
    def _circle_contains(
        center: tuple[int, int],
        position: tuple[int, int],
    ) -> bool:
        return hypot(position[0] - center[0], position[1] - center[1]) <= (
            TowerActionMenu._BUTTON_RADIUS + TowerActionMenu._HOVER_RADIUS_BONUS + 2
        )
