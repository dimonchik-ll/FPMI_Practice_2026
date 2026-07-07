from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot, UiAction, UiActionKind
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import UiComponent, draw_centered_text


class PauseControl(UiComponent):
    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts
        self._is_hovered = False

    def handle_event(
        self,
        event: pygame.event.Event,
        snapshot: GameSnapshot | None,
    ) -> UiAction | None:
        if event.type == pygame.MOUSEMOTION:
            self._is_hovered = self._layout.pause_button.collidepoint(event.pos)
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        self._is_hovered = self._layout.pause_button.collidepoint(event.pos)
        if snapshot is None or not self._can_pause(snapshot) or not self._is_hovered:
            return None

        return UiAction(UiActionKind.PAUSE)

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self._is_hovered = self._layout.pause_button.collidepoint(pygame.mouse.get_pos())
        fill, border, text_color = self._button_style(snapshot)
        rect = self._layout.pause_button
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
        draw_centered_text(
            surface,
            "ПАУЗА  [P]",
            self._fonts.section,
            text_color,
            rect,
        )

    def _button_style(self, snapshot: GameSnapshot) -> tuple[Color, Color, Color]:
        if not self._can_pause(snapshot):
            return (
                (66, 70, 76),
                (108, 112, 119),
                (179, 182, 186),
            )

        fill: Color = (83, 81, 126) if self._is_hovered else (68, 67, 108)
        return fill, (203, 194, 241), (246, 244, 255)

    @staticmethod
    def _can_pause(snapshot: GameSnapshot) -> bool:
        return not snapshot.paused and not snapshot.game_over and not snapshot.victory
