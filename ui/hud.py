from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import UiComponent, draw_centered_text, draw_text


class HudPanel(UiComponent):
    _SHADOW_WIDTH = 10

    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        if self._layout.visible_panel.width > 0:
            self._draw_panel_background(surface)
            self._draw_header(surface, snapshot)
        self._draw_toggle_button(surface)

    def _draw_panel_background(self, surface: pygame.Surface) -> None:
        panel = self._layout.panel
        shadow_rect = pygame.Rect(
            panel.x - self._SHADOW_WIDTH,
            panel.y,
            self._SHADOW_WIDTH,
            panel.height,
        )
        shadow = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 70))
        surface.blit(shadow, shadow_rect.topleft)
        pygame.draw.rect(
            surface,
            self._theme.panel_background,
            panel,
        )
        pygame.draw.line(
            surface,
            self._theme.panel_border,
            (panel.x, 0),
            (panel.x, self._layout.height),
            2,
        )

    def _draw_toggle_button(self, surface: pygame.Surface) -> None:
        rect = self._layout.hud_toggle_button
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill: Color = (48, 61, 70) if hovered else (37, 49, 57)
        border: Color = (181, 205, 184) if hovered else self._theme.panel_border
        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=10)
        arrow = "›" if self._layout.hud_open else "‹"
        draw_centered_text(
            surface,
            arrow,
            self._fonts.title,
            self._theme.title_text,
            rect,
        )

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
        if snapshot.paused:
            return "ПАУЗА", (177, 157, 224)
        if snapshot.wave_is_active:
            return "В БОЮ", (232, 189, 93)
        return "ПОДГОТОВКА", (124, 176, 208)
