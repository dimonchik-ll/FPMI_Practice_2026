from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import UiComponent, draw_text, draw_text_right


class GameStatsPanel(UiComponent):
    def __init__(
        self,
        layout: UiLayout,
        theme: UiTheme,
        fonts: UiFonts,
    ) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts

    def contains_point(self, position: tuple[int, int]) -> bool:
        return self._layout.map_stats_panel.collidepoint(position)

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        panel = self._layout.map_stats_panel

        if panel.width <= 0:
            return

        background = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(
            background,
            (18, 28, 34, 220),
            background.get_rect(),
            border_radius=10,
        )
        surface.blit(background, panel.topleft)

        pygame.draw.rect(
            surface,
            self._theme.panel_border,
            panel,
            width=1,
            border_radius=10,
        )

        stats = (
            ("Золото", snapshot.player.money, (232, 196, 102)),
            ("Жизни", snapshot.player.lives, (222, 113, 105)),
            ("Волна", snapshot.wave_number, (129, 185, 221)),
            ("Счёт", snapshot.player.score, (155, 209, 155)),
        )

        for index, (label, value, color) in enumerate(stats):
            self._draw_stat(surface, index, label, value, color)

    def _draw_stat(
        self,
        surface: pygame.Surface,
        index: int,
        label: str,
        value: int,
        color: Color,
    ) -> None:
        rect = self._layout.map_stat_card_rect(index)

        pygame.draw.rect(
            surface,
            (38, 53, 62),
            rect,
            border_radius=7,
        )
        pygame.draw.rect(
            surface,
            color,
            rect,
            width=1,
            border_radius=7,
        )

        pygame.draw.circle(
            surface,
            color,
            (rect.x + 9, rect.centery),
            3,
        )

        draw_text(
            surface,
            label,
            self._fonts.small,
            self._theme.muted_text,
            (rect.x + 17, rect.y + 5),
        )

        draw_text_right(
            surface,
            str(value),
            self._fonts.small,
            self._theme.body_text,
            (rect.right - 8, rect.y + 5),
        )