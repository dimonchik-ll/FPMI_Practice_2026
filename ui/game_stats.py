from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import UiComponent, draw_text, draw_text_right


def format_compact_number(value: int | float) -> str:
    sign = "-" if value < 0 else ""
    number = abs(float(value))

    units = (
        (1_000_000_000_000, "т"),
        (1_000_000_000, "б"),
        (1_000_000, "м"),
        (1_000, "к"),
    )

    for divider, suffix in units:
        if number >= divider:
            compact = number / divider
            if compact >= 100 or compact.is_integer():
                text = f"{compact:.0f}"
            else:
                text = f"{compact:.1f}".rstrip("0").rstrip(".")
            return f"{sign}{text}{suffix}"

    return f"{int(value)}"


class GameStatsPanel(UiComponent):
    _LABELS = (
        "Gold",
        "HP",
        "Wave",
        "Score",
    )

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
            (*self._theme.panel_background, 230),
            background.get_rect(),
            border_bottom_right_radius=10,
        )
        surface.blit(background, panel.topleft)
        pygame.draw.rect(
            surface,
            self._theme.panel_border,
            panel,
            width=1,
            border_bottom_right_radius=10,
        )

        stats = (
            (snapshot.player.money, (232, 196, 102)),
            (snapshot.player.lives, (222, 113, 105)),
            (snapshot.wave_number, (129, 185, 221)),
            (snapshot.player.score, (155, 209, 155)),
        )
        for index, (value, color) in enumerate(stats):
            rect = self._layout.map_stat_card_rect(index)
            if index > 0:
                pygame.draw.line(
                    surface,
                    self._theme.panel_border,
                    (rect.x, rect.y + 7),
                    (rect.x, rect.bottom - 7),
                    1,
                )
            self._draw_stat(
                surface,
                rect,
                self._LABELS[index],
                value,
                color,
            )

    def _draw_stat(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        value: int,
        color: Color,
    ) -> None:
        dot_x = rect.x + 8
        text_y = rect.y + 5
        pygame.draw.circle(
            surface,
            color,
            (dot_x, rect.centery),
            3,
        )
        draw_text(
            surface,
            label,
            self._fonts.small,
            self._theme.muted_text,
            (dot_x + 5, text_y),
        )
        draw_text_right(
            surface,
            format_compact_number(value),
            self._fonts.small,
            self._theme.body_text,
            (rect.right - 7, text_y),
        )
