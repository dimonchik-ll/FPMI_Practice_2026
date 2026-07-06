from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import UiComponent, draw_centered_text, draw_text


class HudPanel(UiComponent):
    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        pygame.draw.rect(
            surface,
            self._theme.panel_background,
            self._layout.panel,
        )

        pygame.draw.line(
            surface,
            self._theme.panel_border,
            (self._layout.map_width, 0),
            (self._layout.map_width, self._layout.height),
            2,
        )

        self._draw_header(surface, snapshot)

    def _draw_header(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        draw_text(
            surface,
            "TOWER DEFENSE",
            self._fonts.title,
            self._theme.title_text,
            self._layout.title_position,
        )

        label, color = self._status(snapshot)
        status_rect = self._layout.status_badge_rect

        pygame.draw.rect(
            surface,
            color,
            status_rect,
            border_radius=8,
        )
        pygame.draw.rect(
            surface,
            self._theme.panel_border,
            status_rect,
            width=1,
            border_radius=8,
        )

        draw_centered_text(
            surface,
            label,
            self._fonts.small,
            (20, 28, 31),
            status_rect,
        )

    @staticmethod
    def _status(snapshot: GameSnapshot) -> tuple[str, Color]:
        if snapshot.game_over:
            return "ПОРАЖЕНИЕ", (215, 116, 106)

        if snapshot.victory:
            return "ПОБЕДА", (129, 190, 122)

        if snapshot.wave_is_active:
            return "В БОЮ", (232, 189, 93)

        return "ПОДГОТОВКА", (124, 176, 208)