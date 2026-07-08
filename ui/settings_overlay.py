from __future__ import annotations

from dataclasses import dataclass

import pygame

from shared.contracts import GameSnapshot, UiAction
from ui.layout import UiLayout
from ui.settings import MenuSettings, load_settings, save_settings
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import UiComponent, draw_centered_text


@dataclass(frozen=True, slots=True)
class _Slider:
    key: str
    rect: pygame.Rect


class SettingsOverlay(UiComponent):
    _WIDTH = 760
    _HEIGHT = 390
    _ROW_GAP = 78

    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts
        self._settings: MenuSettings = load_settings()

        self._is_open = False
        self._hovered_slider: str | None = None
        self._dragged_slider: str | None = None
        self._back_hovered = False

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        self._settings = load_settings()
        self._is_open = True
        self._hovered_slider = None
        self._dragged_slider = None
        self._back_hovered = False

    def close(self) -> None:
        self._is_open = False
        self._hovered_slider = None
        self._dragged_slider = None
        self._back_hovered = False

    def handle_event(
        self,
        event: pygame.event.Event,
        snapshot: GameSnapshot | None,
    ) -> UiAction | None:
        if not self._is_open:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
            return None

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

            if self._dragged_slider is not None:
                self._set_slider_value(self._dragged_slider, event.pos[0])

            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragged_slider = None
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        self._update_hover(event.pos)

        if self._back_button_rect().collidepoint(event.pos):
            self.close()
            return None

        if self._sound_toggle_rect().collidepoint(event.pos):
            self._settings.sound_enabled = not self._settings.sound_enabled
            self._save_settings()
            return None

        if self._music_toggle_rect().collidepoint(event.pos):
            self._settings.music_enabled = not self._settings.music_enabled
            self._save_settings()
            return None

        if self._hints_toggle_rect().collidepoint(event.pos):
            self._settings.show_menu_hints = not self._settings.show_menu_hints
            self._save_settings()
            return None

        for slider in self._settings_sliders():
            if slider.rect.inflate(0, 18).collidepoint(event.pos):
                self._dragged_slider = slider.key
                self._set_slider_value(slider.key, event.pos[0])
                return None

        return None

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        if not self._is_open:
            return

        self._draw_backdrop(surface)

        modal = self._modal_rect()
        pygame.draw.rect(surface, (29, 43, 54), modal, border_radius=14)
        pygame.draw.rect(
            surface,
            self._theme.panel_border,
            modal,
            width=2,
            border_radius=14,
        )

        draw_centered_text(
            surface,
            "НАСТРОЙКИ",
            self._fonts.title,
            self._theme.title_text,
            pygame.Rect(modal.x, modal.y + 22, modal.width, 38),
        )

        draw_centered_text(
            surface,
            "ESC или кнопка назад вернут в меню паузы.",
            self._fonts.small,
            self._theme.muted_text,
            pygame.Rect(modal.x, modal.y + 66, modal.width, 24),
        )

        self._draw_settings_table(surface)
        self._draw_back_button(surface)

    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((3, 8, 13, 184))
        surface.blit(overlay, (0, 0))

    def _draw_settings_table(self, surface: pygame.Surface) -> None:
        self._draw_setting_row(
            surface,
            row_index=0,
            label="ЗВУК",
            toggle_rect=self._sound_toggle_rect(),
            enabled=self._settings.sound_enabled,
            slider=self._sound_slider(),
            volume=self._settings.sound_volume,
        )

        self._draw_setting_row(
            surface,
            row_index=1,
            label="МУЗЫКА",
            toggle_rect=self._music_toggle_rect(),
            enabled=self._settings.music_enabled,
            slider=self._music_slider(),
            volume=self._settings.music_volume,
        )

        self._draw_setting_row(
            surface,
            row_index=2,
            label="ПОДСКАЗКИ В МЕНЮ",
            toggle_rect=self._hints_toggle_rect(),
            enabled=self._settings.show_menu_hints,
            slider=None,
            volume=None,
        )

    def _draw_setting_row(
        self,
        surface: pygame.Surface,
        row_index: int,
        label: str,
        toggle_rect: pygame.Rect,
        enabled: bool,
        slider: _Slider | None,
        volume: int | None,
    ) -> None:
        label_rect = self._setting_label_rect(row_index)

        label_surface = self._fonts.body.render(
            label,
            True,
            self._theme.body_text,
        )
        surface.blit(
            label_surface,
            label_surface.get_rect(midleft=(label_rect.x, label_rect.centery)),
        )

        self._draw_toggle(surface, toggle_rect, enabled)

        if slider is not None and volume is not None:
            self._draw_slider(surface, slider, volume, enabled)
            self._draw_volume_value(
                surface,
                volume,
                self._setting_value_rect(row_index),
                enabled,
            )
        else:
            hint_surface = self._fonts.small.render(
                "—",
                True,
                self._theme.muted_text,
            )
            surface.blit(
                hint_surface,
                hint_surface.get_rect(center=self._setting_slider_area(row_index).center),
            )

        if row_index < 2:
            table = self._settings_table_rect()
            separator_y = table.y + 62 + row_index * self._ROW_GAP
            pygame.draw.line(
                surface,
                (33, 49, 55),
                (table.x, separator_y),
                (table.right, separator_y),
                1,
            )

    def _draw_toggle(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        enabled: bool,
    ) -> None:
        is_hovered = rect.collidepoint(pygame.mouse.get_pos())

        fill: Color = (76, 132, 86) if enabled else (64, 70, 77)
        border: Color = (
            self._theme.hover_card_border
            if is_hovered
            else self._theme.default_card_border
        )

        text = "ВКЛ" if enabled else "ВЫКЛ"

        pygame.draw.rect(surface, fill, rect, border_radius=14)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=14)

        draw_centered_text(
            surface,
            text,
            self._fonts.small,
            self._theme.body_text,
            rect,
        )

    def _draw_slider(
        self,
        surface: pygame.Surface,
        slider: _Slider,
        volume: int,
        enabled: bool,
    ) -> None:
        rect = slider.rect
        is_active = self._dragged_slider == slider.key
        is_hovered = self._hovered_slider == slider.key or is_active

        track_y = rect.centery
        fill_width = round(rect.width * volume / 100)
        handle_x = rect.x + fill_width

        track_color: Color = (50, 62, 72) if enabled else (42, 47, 52)
        fill_color: Color = (107, 171, 116) if enabled else (84, 96, 91)
        handle_border: Color = (
            self._theme.hover_card_border
            if is_hovered
            else self._theme.default_card_border
        )

        pygame.draw.line(
            surface,
            track_color,
            (rect.x, track_y),
            (rect.right, track_y),
            8,
        )

        pygame.draw.line(
            surface,
            fill_color,
            (rect.x, track_y),
            (rect.x + fill_width, track_y),
            8,
        )

        pygame.draw.circle(surface, handle_border, (handle_x, track_y), 12)
        pygame.draw.circle(surface, fill_color, (handle_x, track_y), 8)

    def _draw_volume_value(
        self,
        surface: pygame.Surface,
        volume: int,
        rect: pygame.Rect,
        enabled: bool,
    ) -> None:
        color: Color = self._theme.body_text if enabled else self._theme.muted_text
        value_surface = self._fonts.small.render(f"{volume}%", True, color)

        surface.blit(
            value_surface,
            value_surface.get_rect(midright=(rect.right, rect.centery)),
        )

    def _draw_back_button(self, surface: pygame.Surface) -> None:
        rect = self._back_button_rect()
        self._back_hovered = rect.collidepoint(pygame.mouse.get_pos())

        fill: Color = self._theme.hover_card if self._back_hovered else self._theme.default_card
        border: Color = (
            self._theme.hover_card_border
            if self._back_hovered
            else self._theme.default_card_border
        )

        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=10)

        draw_centered_text(
            surface,
            "НАЗАД",
            self._fonts.section,
            self._theme.body_text,
            rect,
        )

    def _modal_rect(self) -> pygame.Rect:
        screen = self._layout.window_rect

        width = min(self._WIDTH, max(320, screen.width - 48))
        height = min(self._HEIGHT, max(300, screen.height - 48))

        rect = pygame.Rect(0, 0, width, height)
        rect.center = screen.center

        return rect

    def _settings_table_rect(self) -> pygame.Rect:
        modal = self._modal_rect()

        return pygame.Rect(
            modal.x + 36,
            modal.y + 106,
            modal.width - 72,
            238,
        )

    def _settings_row_y(self, index: int) -> int:
        table = self._settings_table_rect()
        return table.y + index * self._ROW_GAP

    def _setting_label_rect(self, index: int) -> pygame.Rect:
        table = self._settings_table_rect()

        return pygame.Rect(
            table.x,
            self._settings_row_y(index),
            250,
            48,
        )

    def _setting_toggle_rect(self, index: int) -> pygame.Rect:
        table = self._settings_table_rect()

        return pygame.Rect(
            table.x + 270,
            self._settings_row_y(index) + 3,
            104,
            42,
        )

    def _setting_slider_area(self, index: int) -> pygame.Rect:
        table = self._settings_table_rect()
        x = table.x + 410
        width = max(120, table.right - x - 64)

        return pygame.Rect(
            x,
            self._settings_row_y(index) + 13,
            width,
            22,
        )

    def _setting_value_rect(self, index: int) -> pygame.Rect:
        table = self._settings_table_rect()

        return pygame.Rect(
            table.right - 56,
            self._settings_row_y(index) + 5,
            56,
            40,
        )

    def _back_button_rect(self) -> pygame.Rect:
        modal = self._modal_rect()
        width = min(300, modal.width - 72)

        return pygame.Rect(
            modal.centerx - width // 2,
            modal.bottom - 64,
            width,
            44,
        )

    def _sound_toggle_rect(self) -> pygame.Rect:
        return self._setting_toggle_rect(0)

    def _music_toggle_rect(self) -> pygame.Rect:
        return self._setting_toggle_rect(1)

    def _hints_toggle_rect(self) -> pygame.Rect:
        return self._setting_toggle_rect(2)

    def _sound_slider(self) -> _Slider:
        return _Slider("sound_volume", self._setting_slider_area(0))

    def _music_slider(self) -> _Slider:
        return _Slider("music_volume", self._setting_slider_area(1))

    def _settings_sliders(self) -> tuple[_Slider, ...]:
        return self._sound_slider(), self._music_slider()

    def _set_slider_value(self, key: str, mouse_x: int) -> None:
        slider = next(item for item in self._settings_sliders() if item.key == key)

        ratio = (mouse_x - slider.rect.x) / slider.rect.width
        value = max(0, min(100, round(ratio * 100)))

        if key == "sound_volume" and self._settings.sound_volume != value:
            self._settings.sound_volume = value
            self._save_settings()

        elif key == "music_volume" and self._settings.music_volume != value:
            self._settings.music_volume = value
            self._save_settings()

    def _update_hover(self, position: tuple[int, int]) -> None:
        self._hovered_slider = None
        self._back_hovered = self._back_button_rect().collidepoint(position)

        for slider in self._settings_sliders():
            if slider.rect.inflate(0, 18).collidepoint(position):
                self._hovered_slider = slider.key
                return

    def _save_settings(self) -> None:
        save_settings(self._settings)
