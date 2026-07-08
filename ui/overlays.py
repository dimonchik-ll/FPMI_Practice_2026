from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot, UiAction, UiActionKind
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import UiComponent, draw_centered_text


class _BaseOverlay(UiComponent):
    _MODAL_WIDTH = 360

    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts

    def _modal_rect(self, height: int) -> pygame.Rect:
        screen_rect = self._layout.window_rect
        width = min(self._MODAL_WIDTH, max(240, screen_rect.width - 36))
        rect = pygame.Rect(0, 0, width, height)
        rect.center = screen_rect.center

        return rect

    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((3, 8, 13, 184))
        surface.blit(overlay, (0, 0))

    def _draw_modal(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (29, 43, 54), rect, border_radius=14)
        pygame.draw.rect(
            surface,
            self._theme.panel_border,
            rect,
            width=2,
            border_radius=14,
        )

    def _draw_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        fill: Color,
        border: Color,
        hovered: bool,
    ) -> None:
        active_fill = tuple(min(255, value + 14) for value in fill) if hovered else fill

        pygame.draw.rect(surface, active_fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=8)

        draw_centered_text(surface, label, self._fonts.section, (247, 249, 241), rect)


class PauseOverlay(_BaseOverlay):
    _HEIGHT = 332

    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        super().__init__(layout, theme, fonts)
        self._hovered_button: str | None = None

    def handle_event(
        self,
        event: pygame.event.Event,
        snapshot: GameSnapshot | None,
    ) -> UiAction | None:
        if snapshot is None or not snapshot.paused:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                return UiAction(UiActionKind.RESUME)
            if event.key == pygame.K_s:
                return UiAction(UiActionKind.OPEN_SETTINGS)
            if event.key == pygame.K_m:
                return UiAction(UiActionKind.OPEN_MAIN_MENU)
            if event.key == pygame.K_r:
                return UiAction(UiActionKind.RESTART)
            return None

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        self._update_hover(event.pos)

        if self._hovered_button == "resume":
            return UiAction(UiActionKind.RESUME)

        if self._hovered_button == "settings":
            return UiAction(UiActionKind.OPEN_SETTINGS)

        if self._hovered_button == "main_menu":
            return UiAction(UiActionKind.OPEN_MAIN_MENU)

        if self._hovered_button == "restart":
            return UiAction(UiActionKind.RESTART)

        return None

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self._draw_backdrop(surface)

        modal = self._modal_rect(self._HEIGHT)
        self._draw_modal(surface, modal)
        self._update_hover(pygame.mouse.get_pos())

        draw_centered_text(
            surface,
            "МЕНЮ",
            self._fonts.title,
            self._theme.title_text,
            pygame.Rect(modal.x, modal.y + 22, modal.width, 38),
        )

        draw_centered_text(
            surface,
            "Игра остановлена.",
            self._fonts.body,
            self._theme.muted_text,
            pygame.Rect(modal.x, modal.y + 66, modal.width, 26),
        )

        for key, rect, label, fill, border in self._button_specs(modal):
            self._draw_button(
                surface,
                rect,
                label,
                fill,
                border,
                self._hovered_button == key,
            )

    def _button_specs(
        self,
        modal: pygame.Rect,
    ) -> tuple[tuple[str, pygame.Rect, str, Color, Color], ...]:
        width = modal.width - 48
        height = 38
        gap = 12
        x = modal.x + 24
        y = modal.y + 108

        return (
            (
                "resume",
                pygame.Rect(x, y, width, height),
                "ПРОДОЛЖИТЬ [ESC]",
                (70, 122, 78),
                (193, 229, 178),
            ),
            (
                "settings",
                pygame.Rect(x, y + (height + gap), width, height),
                "НАСТРОЙКИ [S]",
                (68, 67, 108),
                (203, 194, 241),
            ),
            (
                "main_menu",
                pygame.Rect(x, y + (height + gap) * 2, width, height),
                "ВЫЙТИ В МЕНЮ [M]",
                (100, 79, 56),
                (222, 186, 121),
            ),
            (
                "restart",
                pygame.Rect(x, y + (height + gap) * 3, width, height),
                "НАЧАТЬ ЗАНОВО [R]",
                (116, 58, 57),
                (223, 137, 128),
            ),
        )

    def _update_hover(self, position: tuple[int, int]) -> None:
        self._hovered_button = None

        modal = self._modal_rect(self._HEIGHT)

        for key, rect, _, _, _ in self._button_specs(modal):
            if rect.collidepoint(position):
                self._hovered_button = key
                return


class EndGameOverlay(_BaseOverlay):
    _HEIGHT = 236

    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        super().__init__(layout, theme, fonts)
        self._restart_hovered = False

    def handle_event(
        self,
        event: pygame.event.Event,
        snapshot: GameSnapshot | None,
    ) -> UiAction | None:
        if snapshot is None or not (snapshot.game_over or snapshot.victory):
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            return UiAction(UiActionKind.RESTART)

        if event.type == pygame.MOUSEMOTION:
            self._restart_hovered = self._restart_button_rect().collidepoint(event.pos)
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        self._restart_hovered = self._restart_button_rect().collidepoint(event.pos)

        if self._restart_hovered:
            return UiAction(UiActionKind.RESTART)

        return None

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self._draw_backdrop(surface)

        modal = self._modal_rect(self._HEIGHT)
        self._draw_modal(surface, modal)
        self._restart_hovered = self._restart_button_rect().collidepoint(
            pygame.mouse.get_pos()
        )

        title = "ПОБЕДА" if snapshot.victory else "ИГРА ОКОНЧЕНА"
        title_color: Color = (171, 222, 171) if snapshot.victory else (238, 150, 132)
        subtitle = (
            "Все волны отражены."
            if snapshot.victory
            else "База больше не выдержала натиск."
        )
        summary = f"Счёт: {snapshot.player.score} Волна: {snapshot.wave_number}"

        draw_centered_text(
            surface,
            title,
            self._fonts.title,
            title_color,
            pygame.Rect(modal.x, modal.y + 24, modal.width, 38),
        )

        draw_centered_text(
            surface,
            subtitle,
            self._fonts.body,
            self._theme.muted_text,
            pygame.Rect(modal.x, modal.y + 73, modal.width, 28),
        )

        draw_centered_text(
            surface,
            summary,
            self._fonts.body,
            self._theme.body_text,
            pygame.Rect(modal.x, modal.y + 108, modal.width, 28),
        )

        self._draw_button(
            surface,
            self._restart_button_rect(),
            "ИГРАТЬ СНОВА [R]",
            (70, 122, 78),
            (193, 229, 178),
            self._restart_hovered,
        )

    def _restart_button_rect(self) -> pygame.Rect:
        modal = self._modal_rect(self._HEIGHT)

        return pygame.Rect(modal.x + 24, modal.y + 160, modal.width - 48, 42)
