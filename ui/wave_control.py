from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot, UiAction, UiActionKind
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import UiComponent, draw_centered_text


class WaveControl(UiComponent):
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
            self._is_hovered = self._layout.start_wave_button.collidepoint(event.pos)
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        self._is_hovered = self._layout.start_wave_button.collidepoint(event.pos)

        if snapshot is None or not self._is_hovered or not self._can_start(snapshot):
            return None

        return UiAction(UiActionKind.START_WAVE)

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self._is_hovered = self._layout.start_wave_button.collidepoint(
            pygame.mouse.get_pos()
        )

        fill, border, label, text_color = self._button_state(snapshot)
        rect = self._layout.start_wave_button

        pygame.draw.rect(surface, fill, rect, border_radius=9)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=9)

        draw_centered_text(
            surface,
            label,
            self._fonts.section,
            text_color,
            rect,
        )

    def _button_state(
        self,
        snapshot: GameSnapshot,
    ) -> tuple[Color, Color, str, Color]:
        if snapshot.game_over or snapshot.victory:
            return (
                (66, 70, 76),
                (108, 112, 119),
                "ИГРА ЗАВЕРШЕНА",
                (179, 182, 186),
            )

        if snapshot.wave_is_active:
            return (
                (66, 80, 86),
                (108, 126, 134),
                "ВОЛНА ИДЁТ",
                (179, 192, 196),
            )

        fill: Color = (85, 143, 92) if self._is_hovered else (69, 120, 78)

        return (
            fill,
            (193, 229, 178),
            "СТАРТ ВОЛНЫ",
            (247, 249, 241),
        )

    @staticmethod
    def _can_start(snapshot: GameSnapshot) -> bool:
        return not snapshot.wave_is_active and not snapshot.game_over and not snapshot.victory