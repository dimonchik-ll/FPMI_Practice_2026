from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pygame

from ui.settings import MenuSettings, load_settings, save_settings
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import draw_centered_text


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MAIN_MENU_BACKGROUND_PATHS = (
    Path("assets/ui/main_menu_background.png"),
    _PROJECT_ROOT / "assets" / "ui" / "main_menu_background.png",
)


@dataclass(frozen=True, slots=True)
class MapMenuOption:
    level_number: int
    title: str
    preview: pygame.Surface


class MainMenuActionKind(str, Enum):
    START_GAME = "start_game"
    QUIT = "quit"


@dataclass(frozen=True, slots=True)
class MainMenuAction:
    kind: MainMenuActionKind
    level_number: int | None = None


class MenuScreen(str, Enum):
    HOME = "home"
    MODES = "modes"
    LEVEL_SELECT = "level_select"
    SETTINGS = "settings"
    ENDLESS_STUB = "endless_stub"


@dataclass(frozen=True, slots=True)
class _MenuButton:
    key: str
    title: str
    rect: pygame.Rect
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class _Slider:
    key: str
    rect: pygame.Rect


class MainMenu:
    def __init__(
        self,
        screen_size: tuple[int, int],
        options: tuple[MapMenuOption, ...],
    ) -> None:
        if not options:
            raise ValueError("Для выбора обычного режима нужна хотя бы одна карта.")

        self._screen_rect = pygame.Rect((0, 0), screen_size)
        self._options = options
        self._theme = UiTheme()
        self._fonts = UiFonts()
        self._settings: MenuSettings = load_settings()
        self._screen = MenuScreen.HOME
        self._selected_level = options[0].level_number
        self._hovered_level: int | None = None
        self._hovered_button: str | None = None
        self._hovered_slider: str | None = None
        self._dragged_slider: str | None = None
        self._focused_button_index = 0
        self._preview_cache: dict[tuple[int, int, int], pygame.Surface] = {}
        self._background_source = self._load_background()
        self._background_cache: pygame.Surface | None = None
        self._background_cache_size: tuple[int, int] | None = None

    @property
    def selected_level(self) -> int:
        return self._selected_level

    def handle_event(self, event: pygame.event.Event) -> MainMenuAction | None:
        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
            if self._dragged_slider is not None:
                self._set_slider_value(self._dragged_slider, event.pos[0])
            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragged_slider = None
            return None

        if event.type == pygame.KEYDOWN:
            return self._handle_key(event.key)

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        self._update_hover(event.pos)

        if self._screen == MenuScreen.SETTINGS:
            if self._handle_settings_click(event.pos):
                return None

        if self._screen == MenuScreen.LEVEL_SELECT:
            if self._hovered_level is not None:
                self._selected_level = self._hovered_level
                return None

        for button in self._buttons_for_current_screen():
            if button.enabled and button.rect.collidepoint(event.pos):
                return self._activate(button.key)

        return None

    def draw(self, surface: pygame.Surface) -> None:
        self._update_hover(pygame.mouse.get_pos())
        self._draw_background(surface)

        if self._screen == MenuScreen.HOME:
            self._draw_home(surface)
        elif self._screen == MenuScreen.MODES:
            self._draw_modes(surface)
        elif self._screen == MenuScreen.LEVEL_SELECT:
            self._draw_level_select(surface)
        elif self._screen == MenuScreen.SETTINGS:
            self._draw_settings(surface)
        elif self._screen == MenuScreen.ENDLESS_STUB:
            self._draw_stub(
                surface,
                title="БЕСКОНЕЧНЫЙ РЕЖИМ",
                message="Бесконечный режим скоро появится.",
            )

    def _handle_key(self, key: int) -> MainMenuAction | None:
        if key == pygame.K_ESCAPE:
            return self._go_back()

        if self._screen == MenuScreen.LEVEL_SELECT:
            if key in (pygame.K_LEFT, pygame.K_UP):
                self._move_level_selection(-1)
                return None
            if key in (pygame.K_RIGHT, pygame.K_DOWN):
                self._move_level_selection(1)
                return None
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                return MainMenuAction(
                    MainMenuActionKind.START_GAME,
                    self._selected_level,
                )
            return None

        buttons = self._buttons_for_current_screen()
        if not buttons:
            return None
        if key in (pygame.K_UP, pygame.K_LEFT):
            self._focused_button_index = (
                self._focused_button_index - 1
            ) % len(buttons)
            return None
        if key in (pygame.K_DOWN, pygame.K_RIGHT):
            self._focused_button_index = (
                self._focused_button_index + 1
            ) % len(buttons)
            return None
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            return self._activate(buttons[self._focused_button_index].key)
        return None

    def _activate(self, key: str) -> MainMenuAction | None:
        if key == "modes":
            self._show(MenuScreen.MODES)
        elif key == "settings":
            self._show(MenuScreen.SETTINGS)
        elif key == "quit":
            return MainMenuAction(MainMenuActionKind.QUIT)
        elif key == "normal":
            self._show(MenuScreen.LEVEL_SELECT)
        elif key == "endless":
            self._show(MenuScreen.ENDLESS_STUB)
        elif key == "start":
            return MainMenuAction(
                MainMenuActionKind.START_GAME,
                self._selected_level,
            )
        elif key == "back_home":
            self._show(MenuScreen.HOME)
        elif key == "back_modes":
            self._show(MenuScreen.MODES)
        return None

    def _go_back(self) -> MainMenuAction | None:
        if self._screen == MenuScreen.HOME:
            return MainMenuAction(MainMenuActionKind.QUIT)
        if self._screen == MenuScreen.MODES:
            self._show(MenuScreen.HOME)
        elif self._screen == MenuScreen.LEVEL_SELECT:
            self._show(MenuScreen.MODES)
        elif self._screen == MenuScreen.SETTINGS:
            self._show(MenuScreen.HOME)
        elif self._screen == MenuScreen.ENDLESS_STUB:
            self._show(MenuScreen.MODES)
        return None

    def _show(self, screen: MenuScreen) -> None:
        self._screen = screen
        self._hovered_level = None
        self._hovered_button = None
        self._hovered_slider = None
        self._dragged_slider = None
        self._focused_button_index = 0

    def _handle_settings_click(self, position: tuple[int, int]) -> bool:
        if self._sound_toggle_rect().collidepoint(position):
            self._settings.sound_enabled = not self._settings.sound_enabled
            self._save_settings()
            return True
        if self._music_toggle_rect().collidepoint(position):
            self._settings.music_enabled = not self._settings.music_enabled
            self._save_settings()
            return True
        if self._hints_toggle_rect().collidepoint(position):
            self._settings.show_menu_hints = not self._settings.show_menu_hints
            self._save_settings()
            return True

        for slider in self._settings_sliders():
            if slider.rect.inflate(0, 18).collidepoint(position):
                self._dragged_slider = slider.key
                self._set_slider_value(slider.key, position[0])
                return True

        return False

    def _set_slider_value(self, key: str, mouse_x: int) -> None:
        slider = next(
            item for item in self._settings_sliders() if item.key == key
        )
        ratio = (mouse_x - slider.rect.x) / slider.rect.width
        value = max(0, min(100, round(ratio * 100)))
        if key == "sound_volume" and self._settings.sound_volume != value:
            self._settings.sound_volume = value
            self._save_settings()
        elif key == "music_volume" and self._settings.music_volume != value:
            self._settings.music_volume = value
            self._save_settings()

    def _save_settings(self) -> None:
        save_settings(self._settings)

    def _load_background(self) -> pygame.Surface | None:
        for path in _MAIN_MENU_BACKGROUND_PATHS:
            if not path.exists():
                continue
            try:
                image = pygame.image.load(str(path))
            except pygame.error:
                continue
            try:
                return image.convert()
            except pygame.error:
                return image
        return None

    def _draw_background(self, surface: pygame.Surface) -> None:
        if self._background_source is None:
            self._draw_fallback_background(surface)
        else:
            screen_size = surface.get_size()
            if (
                self._background_cache is None
                or self._background_cache_size != screen_size
            ):
                self._background_cache = self._scale_background_cover(screen_size)
                self._background_cache_size = screen_size

            surface.blit(self._background_cache, (0, 0))
            overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 72))
            surface.blit(overlay, (0, 0))

        draw_centered_text(
            surface,
            "TOWER DEFENSE",
            self._fonts.title,
            self._theme.title_text,
            pygame.Rect(0, 44, self._screen_rect.width, 44),
        )

    def _scale_background_cover(self, target_size: tuple[int, int]) -> pygame.Surface:
        if self._background_source is None:
            canvas = pygame.Surface(target_size)
            canvas.fill((12, 21, 28))
            return canvas

        source_width, source_height = self._background_source.get_size()
        target_width, target_height = target_size
        scale = max(target_width / source_width, target_height / source_height)
        scaled_size = (
            max(1, round(source_width * scale)),
            max(1, round(source_height * scale)),
        )
        scaled = pygame.transform.scale(self._background_source, scaled_size)
        canvas = pygame.Surface(target_size)
        canvas.blit(
            scaled,
            scaled.get_rect(center=(target_width // 2, target_height // 2)),
        )
        return canvas

    def _draw_fallback_background(self, surface: pygame.Surface) -> None:
        surface.fill((12, 21, 28))
        pygame.draw.rect(
            surface,
            (18, 33, 43),
            pygame.Rect(0, 0, self._screen_rect.width, 156),
        )
        pygame.draw.line(
            surface,
            self._theme.panel_border,
            (0, 156),
            (self._screen_rect.width, 156),
            2,
        )
        pygame.draw.circle(
            surface,
            (35, 65, 58),
            (self._screen_rect.width - 90, 68),
            170,
        )
        pygame.draw.circle(
            surface,
            (29, 51, 67),
            (78, self._screen_rect.height - 38),
            150,
        )

    def _draw_home(self, surface: pygame.Surface) -> None:
        draw_centered_text(
            surface,
            "ГЛАВНОЕ МЕНЮ",
            self._fonts.section,
            self._theme.muted_text,
            pygame.Rect(0, 102, self._screen_rect.width, 30),
        )
        self._draw_buttons(surface)
        self._draw_footer(surface, "ENTER: выбрать ESC: выход")

    def _draw_modes(self, surface: pygame.Surface) -> None:
        draw_centered_text(
            surface,
            "ВЫБЕРИТЕ РЕЖИМ",
            self._fonts.section,
            self._theme.muted_text,
            pygame.Rect(0, 102, self._screen_rect.width, 30),
        )
        self._draw_buttons(surface)
        self._draw_footer(surface, "ESC: назад")

    def _draw_level_select(self, surface: pygame.Surface) -> None:
        draw_centered_text(
            surface,
            "ОБЫЧНЫЙ РЕЖИМ — ВЫБОР КАРТЫ",
            self._fonts.section,
            self._theme.muted_text,
            pygame.Rect(0, 102, self._screen_rect.width, 30),
        )
        for option, card_rect in zip(
            self._options,
            self._card_rects(),
            strict=True,
        ):
            self._draw_map_card(surface, option, card_rect)
        self._draw_buttons(surface)
        self._draw_footer(surface, "← →: карта ENTER: начать ESC: назад")

    def _draw_settings(self, surface: pygame.Surface) -> None:
        draw_centered_text(
            surface,
            "НАСТРОЙКИ",
            self._fonts.section,
            self._theme.muted_text,
            pygame.Rect(0, 102, self._screen_rect.width, 30),
        )
        self._draw_settings_table(surface)
        self._draw_buttons(surface)
        self._draw_footer(surface, "ESC: назад")

    def _draw_stub(
        self,
        surface: pygame.Surface,
        title: str,
        message: str,
    ) -> None:
        content = pygame.Rect(
            0,
            0,
            self._screen_rect.width,
            self._screen_rect.height,
        )
        draw_centered_text(
            surface,
            title,
            self._fonts.section,
            self._theme.title_text,
            pygame.Rect(0, content.centery - 100, content.width, 34),
        )
        draw_centered_text(
            surface,
            message,
            self._fonts.body,
            self._theme.muted_text,
            pygame.Rect(0, content.centery - 50, content.width, 34),
        )
        self._draw_buttons(surface)
        self._draw_footer(surface, "ESC: назад")

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
        table = self._settings_table_rect()
        label_rect = self._setting_label_rect(row_index)
        self._draw_setting_label(surface, label, label_rect)
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
            self._draw_empty_slider_slot(surface, self._setting_slider_area(row_index))

        if row_index < 2:
            separator_y = table.y + 62 + row_index * self._settings_row_gap()
            pygame.draw.line(
                surface,
                (33, 49, 55),
                (table.x, separator_y),
                (table.right, separator_y),
                1,
            )

    def _draw_setting_label(
        self,
        surface: pygame.Surface,
        text: str,
        rect: pygame.Rect,
    ) -> None:
        label_surface = self._fonts.body.render(
            text,
            True,
            self._theme.body_text,
        )
        surface.blit(
            label_surface,
            label_surface.get_rect(midleft=(rect.x, rect.centery)),
        )

    def _draw_volume_value(
        self,
        surface: pygame.Surface,
        volume: int,
        rect: pygame.Rect,
        enabled: bool,
    ) -> None:
        color: Color = self._theme.body_text if enabled else self._theme.muted_text
        value_surface = self._fonts.small.render(
            f"{volume}%",
            True,
            color,
        )
        surface.blit(
            value_surface,
            value_surface.get_rect(midright=(rect.right, rect.centery)),
        )

    def _draw_empty_slider_slot(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        hint_surface = self._fonts.small.render(
            "—",
            True,
            self._theme.muted_text,
        )
        surface.blit(hint_surface, hint_surface.get_rect(center=rect.center))

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

    def _draw_map_card(
        self,
        surface: pygame.Surface,
        option: MapMenuOption,
        rect: pygame.Rect,
    ) -> None:
        is_selected = option.level_number == self._selected_level
        is_hovered = option.level_number == self._hovered_level
        if is_selected:
            fill = self._theme.selected_card
            border = self._theme.selected_card_border
            border_width = 4
        elif is_hovered:
            fill = self._theme.hover_card
            border = self._theme.hover_card_border
            border_width = 3
        else:
            fill = self._theme.default_card
            border = self._theme.default_card_border
            border_width = 2

        pygame.draw.rect(surface, fill, rect, border_radius=14)
        pygame.draw.rect(surface, border, rect, width=border_width, border_radius=14)

        preview_rect = pygame.Rect(
            rect.x + 16,
            rect.y + 16,
            rect.width - 32,
            min(188, rect.height - 128),
        )
        pygame.draw.rect(
            surface,
            self._theme.hint_background,
            preview_rect,
            border_radius=9,
        )
        pygame.draw.rect(
            surface,
            self._theme.hint_border,
            preview_rect,
            width=2,
            border_radius=9,
        )
        preview = self._preview_for(option, preview_rect.size)
        surface.blit(preview, preview.get_rect(center=preview_rect.center))

        draw_centered_text(
            surface,
            option.title,
            self._fonts.section,
            self._theme.title_text,
            pygame.Rect(rect.x, preview_rect.bottom + 12, rect.width, 30),
        )
        status = "ВЫБРАНО" if is_selected else "НАЖМИТЕ, ЧТОБЫ ВЫБРАТЬ"
        status_color: Color = (
            (210, 238, 185) if is_selected else self._theme.muted_text
        )
        draw_centered_text(
            surface,
            status,
            self._fonts.small,
            status_color,
            pygame.Rect(rect.x, preview_rect.bottom + 48, rect.width, 24),
        )

    def _draw_buttons(self, surface: pygame.Surface) -> None:
        for index, button in enumerate(self._buttons_for_current_screen()):
            is_hovered = button.key == self._hovered_button
            is_focused = index == self._focused_button_index
            self._draw_button(surface, button, is_hovered, is_focused)

    def _draw_button(
        self,
        surface: pygame.Surface,
        button: _MenuButton,
        is_hovered: bool,
        is_focused: bool,
    ) -> None:
        fill: Color = self._theme.default_card
        border: Color = self._theme.default_card_border
        text_color: Color = self._theme.body_text
        border_width = 2
        if is_focused or is_hovered:
            fill = self._theme.hover_card
            border = self._theme.hover_card_border
            border_width = 3
        if button.key == "start":
            fill = (73, 130, 82) if not is_hovered else (91, 150, 97)
            border = (196, 232, 179)
            text_color = (250, 250, 243)
            border_width = 3

        pygame.draw.rect(surface, fill, button.rect, border_radius=10)
        pygame.draw.rect(
            surface,
            border,
            button.rect,
            width=border_width,
            border_radius=10,
        )
        draw_centered_text(
            surface,
            button.title,
            self._fonts.section,
            text_color,
            button.rect,
        )

    def _draw_footer(self, surface: pygame.Surface, text: str) -> None:
        if not self._settings.show_menu_hints:
            return
        draw_centered_text(
            surface,
            text,
            self._fonts.small,
            self._theme.muted_text,
            pygame.Rect(
                0,
                self._screen_rect.bottom - 40,
                self._screen_rect.width,
                24,
            ),
        )

    def _buttons_for_current_screen(self) -> tuple[_MenuButton, ...]:
        if self._screen == MenuScreen.HOME:
            return self._stacked_buttons(
                (
                    ("modes", "РЕЖИМЫ"),
                    ("settings", "НАСТРОЙКИ"),
                    ("quit", "ВЫХОД"),
                )
            )
        if self._screen == MenuScreen.MODES:
            return self._stacked_buttons(
                (
                    ("normal", "ОБЫЧНЫЙ РЕЖИМ"),
                    ("endless", "БЕСКОНЕЧНЫЙ РЕЖИМ"),
                    ("back_home", "НАЗАД"),
                )
            )
        if self._screen == MenuScreen.LEVEL_SELECT:
            return self._bottom_buttons(
                (
                    ("start", "НАЧАТЬ ИГРУ"),
                    ("back_modes", "НАЗАД"),
                )
            )
        if self._screen == MenuScreen.SETTINGS:
            return self._settings_buttons()
        return self._bottom_buttons((("back_modes", "НАЗАД"),))

    def _stacked_buttons(
        self,
        descriptions: tuple[tuple[str, str], ...],
    ) -> tuple[_MenuButton, ...]:
        width = min(390, self._screen_rect.width - 64)
        height = 58
        gap = 16
        total_height = height * len(descriptions) + gap * (len(descriptions) - 1)
        top = self._screen_rect.centery - total_height // 2 + 52
        return tuple(
            _MenuButton(
                key=key,
                title=title,
                rect=pygame.Rect(
                    (self._screen_rect.width - width) // 2,
                    top + index * (height + gap),
                    width,
                    height,
                ),
            )
            for index, (key, title) in enumerate(descriptions)
        )

    def _bottom_buttons(
        self,
        descriptions: tuple[tuple[str, str], ...],
    ) -> tuple[_MenuButton, ...]:
        width = min(380, self._screen_rect.width - 64)
        height = 50
        gap = 12
        total_height = height * len(descriptions) + gap * (len(descriptions) - 1)
        top = self._screen_rect.bottom - 116 - total_height
        return tuple(
            _MenuButton(
                key=key,
                title=title,
                rect=pygame.Rect(
                    (self._screen_rect.width - width) // 2,
                    top + index * (height + gap),
                    width,
                    height,
                ),
            )
            for index, (key, title) in enumerate(descriptions)
        )

    def _settings_buttons(self) -> tuple[_MenuButton, ...]:
        table = self._settings_table_rect()
        width = min(300, self._screen_rect.width - 64)
        height = 50
        return (
            _MenuButton(
                key="back_home",
                title="НАЗАД",
                rect=pygame.Rect(
                    (self._screen_rect.width - width) // 2,
                    min(table.bottom + 42, self._screen_rect.bottom - 96),
                    width,
                    height,
                ),
            ),
        )

    def _settings_table_rect(self) -> pygame.Rect:
        width = min(780, self._screen_rect.width - 80)
        height = 238
        rect = pygame.Rect(0, 0, width, height)
        rect.centerx = self._screen_rect.centerx
        rect.y = min(
            188,
            max(144, self._screen_rect.height - height - 158),
        )
        return rect

    def _settings_panel_rect(self) -> pygame.Rect:
        return self._settings_table_rect()

    def _settings_row_gap(self) -> int:
        return 78

    def _settings_row_y(self, index: int) -> int:
        table = self._settings_table_rect()
        return table.y + index * self._settings_row_gap()

    def _setting_label_rect(self, index: int) -> pygame.Rect:
        table = self._settings_table_rect()
        return pygame.Rect(
            table.x,
            self._settings_row_y(index),
            260,
            48,
        )

    def _setting_toggle_rect(self, index: int) -> pygame.Rect:
        table = self._settings_table_rect()
        width = 116
        height = 42
        return pygame.Rect(
            table.x + 292,
            self._settings_row_y(index) + 3,
            width,
            height,
        )

    def _setting_slider_area(self, index: int) -> pygame.Rect:
        table = self._settings_table_rect()
        return pygame.Rect(
            table.x + 442,
            self._settings_row_y(index) + 13,
            min(270, table.right - table.x - 442 - 68),
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
        return (self._sound_slider(), self._music_slider())

    def _card_rects(self) -> tuple[pygame.Rect, ...]:
        count = len(self._options)
        horizontal_gap = 24
        outer_margin = 48
        max_width = min(1100, self._screen_rect.width - outer_margin * 2)
        card_width = (max_width - horizontal_gap * (count - 1)) // count
        card_height = min(300, max(235, self._screen_rect.height - 405))
        total_width = card_width * count + horizontal_gap * (count - 1)
        left = (self._screen_rect.width - total_width) // 2
        top = 158
        return tuple(
            pygame.Rect(
                left + index * (card_width + horizontal_gap),
                top,
                card_width,
                card_height,
            )
            for index in range(count)
        )

    def _update_hover(self, position: tuple[int, int]) -> None:
        self._hovered_button = None
        self._hovered_level = None
        self._hovered_slider = None

        if self._screen == MenuScreen.LEVEL_SELECT:
            for option, rect in zip(
                self._options,
                self._card_rects(),
                strict=True,
            ):
                if rect.collidepoint(position):
                    self._hovered_level = option.level_number
                    return

        if self._screen == MenuScreen.SETTINGS:
            for slider in self._settings_sliders():
                if slider.rect.inflate(0, 18).collidepoint(position):
                    self._hovered_slider = slider.key
                    return

        for button in self._buttons_for_current_screen():
            if button.rect.collidepoint(position):
                self._hovered_button = button.key
                return

    def _move_level_selection(self, direction: int) -> None:
        current_index = next(
            index
            for index, option in enumerate(self._options)
            if option.level_number == self._selected_level
        )
        next_index = (current_index + direction) % len(self._options)
        self._selected_level = self._options[next_index].level_number

    def _preview_for(
        self,
        option: MapMenuOption,
        target_size: tuple[int, int],
    ) -> pygame.Surface:
        cache_key = (option.level_number, target_size[0], target_size[1])
        cached = self._preview_cache.get(cache_key)
        if cached is not None:
            return cached

        source = option.preview
        source_width, source_height = source.get_size()
        target_width, target_height = target_size
        scale = min(target_width / source_width, target_height / source_height)
        scaled_size = (
            max(1, round(source_width * scale)),
            max(1, round(source_height * scale)),
        )
        scaled = pygame.transform.scale(source, scaled_size)
        canvas = pygame.Surface(target_size)
        canvas.fill(self._theme.hint_background)
        canvas.blit(
            scaled,
            scaled.get_rect(center=(target_width // 2, target_height // 2)),
        )
        self._preview_cache[cache_key] = canvas
        return canvas
