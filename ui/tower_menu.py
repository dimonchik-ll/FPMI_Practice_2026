from __future__ import annotations

import pygame

from shared.contracts import (
    BUILDABLE_TOWER_KINDS,
    GameSnapshot,
    TOWER_DEFINITIONS,
    TowerKind,
    UiAction,
    UiActionKind,
)
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.tower_info import TowerInfoPanel
from ui.widgets import UiComponent, draw_text, draw_text_right


class TowerMenu(UiComponent):
    _SCROLLBAR_WIDTH = 5
    _SCROLLBAR_MARGIN = 5
    _MIN_SCROLL_THUMB_HEIGHT = 24

    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts

        # Higher tiers are available only through the tower upgrade menu.
        self._tower_kinds = BUILDABLE_TOWER_KINDS
        self._hovered_tower: TowerKind | None = None
        self._scroll_index = 0
        self._dragging_scrollbar = False

        self._tower_info = TowerInfoPanel(layout, theme, fonts)

    def handle_event(
        self,
        event: pygame.event.Event,
        snapshot: GameSnapshot | None,
    ) -> UiAction | None:
        if event.type == pygame.MOUSEWHEEL:
            if self._layout.tower_list_viewport.collidepoint(pygame.mouse.get_pos()):
                self._scroll_by(-event.y)
            return None

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

            if self._dragging_scrollbar:
                self._set_scroll_from_pointer(event.pos[1])

            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_scrollbar = False
            return None

        if event.type != pygame.MOUSEBUTTONDOWN:
            return None

        if event.button in (4, 5):
            if self._layout.tower_list_viewport.collidepoint(event.pos):
                self._scroll_by(-1 if event.button == 5 else 1)
            return None

        if event.button != 1:
            return None

        if self._is_scrollable() and self._scrollbar_track().collidepoint(event.pos):
            self._dragging_scrollbar = True
            self._set_scroll_from_pointer(event.pos[1])
            return None

        self._update_hover(event.pos)

        if self._hovered_tower is None:
            return None

        return UiAction(
            UiActionKind.SELECT_TOWER,
            {"tower_kind": self._hovered_tower},
        )

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self._update_hover(pygame.mouse.get_pos())

        draw_text(
            surface,
            "СТРОИТЕЛЬСТВО",
            self._fonts.section,
            (190, 216, 179),
            self._layout.tower_list_heading_position,
        )

        self._tower_info.draw(
            surface,
            snapshot,
            self._hovered_tower,
        )

        for visible_index, tower_kind in enumerate(self._visible_towers()):
            rect = self._card_rect(visible_index)
            self._draw_card(surface, rect, tower_kind, snapshot)

        self._draw_scrollbar(surface)

    def _visible_towers(self) -> tuple[TowerKind, ...]:
        end = self._scroll_index + self._layout.visible_tower_count
        return self._tower_kinds[self._scroll_index:end]

    def _card_rect(self, visible_index: int) -> pygame.Rect:
        viewport = self._layout.tower_list_viewport

        return pygame.Rect(
            viewport.x,
            viewport.y
            + visible_index * (self._layout.tower_card_height + self._layout.gap),
            viewport.width,
            self._layout.tower_card_height,
        )

    def _draw_card(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        tower_kind: TowerKind,
        snapshot: GameSnapshot,
    ) -> None:
        definition = TOWER_DEFINITIONS[tower_kind]
        selected = snapshot.player.selected_tower == tower_kind
        affordable = snapshot.player.money >= definition.cost
        hovered = self._hovered_tower == tower_kind

        fill, border, text_color = self._card_style(
            selected,
            affordable,
            hovered,
        )

        pygame.draw.rect(surface, fill, rect, border_radius=9)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=9)

        draw_text(
            surface,
            definition.title,
            self._fonts.body,
            text_color,
            (rect.x + 10, rect.y + 4),
        )

        price_color: Color = (
            (235, 202, 118)
            if affordable
            else (205, 133, 127)
        )

        draw_text_right(
            surface,
            f"{definition.cost} мон.",
            self._fonts.small,
            price_color,
            (rect.right - 12, rect.y + 6),
        )

        details = (
            f"Урон {definition.damage} | "
            f"Дальн. {int(definition.attack_range)} | "
            f"{definition.attacks_per_second:.1f}/с"
        )

        details_color: Color = (
            (214, 226, 229)
            if affordable
            else (154, 165, 170)
        )

        draw_text(
            surface,
            details,
            self._fonts.small,
            details_color,
            (rect.x + 10, rect.y + 25),
        )

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        if not self._is_scrollable():
            return

        track = self._scrollbar_track()
        thumb = self._scrollbar_thumb()

        pygame.draw.rect(surface, (29, 40, 48), track, border_radius=3)
        pygame.draw.rect(surface, (160, 190, 199), thumb, border_radius=3)

    def _scrollbar_track(self) -> pygame.Rect:
        viewport = self._layout.tower_list_viewport

        return pygame.Rect(
            viewport.right - self._SCROLLBAR_MARGIN - self._SCROLLBAR_WIDTH,
            viewport.y + self._SCROLLBAR_MARGIN,
            self._SCROLLBAR_WIDTH,
            viewport.height - self._SCROLLBAR_MARGIN * 2,
        )

    def _scrollbar_thumb(self) -> pygame.Rect:
        track = self._scrollbar_track()

        thumb_height = max(
            self._MIN_SCROLL_THUMB_HEIGHT,
            int(
                track.height
                * self._layout.visible_tower_count
                / len(self._tower_kinds)
            ),
        )

        max_offset = self._max_scroll_index()
        movable_height = track.height - thumb_height

        if max_offset == 0:
            thumb_y = track.y
        else:
            thumb_y = track.y + int(
                movable_height * self._scroll_index / max_offset
            )

        return pygame.Rect(
            track.x,
            thumb_y,
            track.width,
            thumb_height,
        )

    def _scroll_by(self, delta: int) -> None:
        self._scroll_index = max(
            0,
            min(
                self._scroll_index + delta,
                self._max_scroll_index(),
            ),
        )

    def _set_scroll_from_pointer(self, pointer_y: int) -> None:
        track = self._scrollbar_track()
        thumb = self._scrollbar_thumb()

        movable_height = track.height - thumb.height

        if movable_height <= 0:
            self._scroll_index = 0
            return

        thumb_top = max(
            track.y,
            min(
                pointer_y - thumb.height // 2,
                track.bottom - thumb.height,
            ),
        )

        progress = (thumb_top - track.y) / movable_height

        self._scroll_index = round(progress * self._max_scroll_index())

    def _update_hover(self, position: tuple[int, int]) -> None:
        self._hovered_tower = None

        for visible_index, tower_kind in enumerate(self._visible_towers()):
            if self._card_rect(visible_index).collidepoint(position):
                self._hovered_tower = tower_kind
                return

    def _is_scrollable(self) -> bool:
        return len(self._tower_kinds) > self._layout.visible_tower_count

    def _max_scroll_index(self) -> int:
        return max(
            0,
            len(self._tower_kinds) - self._layout.visible_tower_count,
        )

    def _card_style(
        self,
        selected: bool,
        affordable: bool,
        hovered: bool,
    ) -> tuple[Color, Color, Color]:
        if selected and affordable:
            return (
                self._theme.selected_card,
                self._theme.selected_card_border,
                self._theme.body_text,
            )

        if selected:
            return (
                self._theme.unavailable_card,
                (210, 151, 138),
                self._theme.body_text,
            )

        if hovered:
            return (
                self._theme.hover_card,
                self._theme.hover_card_border,
                self._theme.body_text,
            )

        if not affordable:
            return (
                self._theme.unavailable_card,
                self._theme.unavailable_card_border,
                self._theme.muted_text,
            )

        return (
            self._theme.default_card,
            self._theme.default_card_border,
            self._theme.body_text,
        )