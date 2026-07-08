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

        self._draw_title_bar(surface)

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
        surface.fill((10, 16, 24))
        pygame.draw.rect(
            surface,
            (29, 42, 48),
            pygame.Rect(0, 0, self._screen_rect.width, self._screen_rect.height),
        )
        pygame.draw.circle(
            surface,
            (48, 67, 54),
            (self._screen_rect.width - 130, 88),
            220,
        )
        pygame.draw.circle(
            surface,
            (56, 38, 68),
            (100, self._screen_rect.height - 30),
            210,
        )
        pygame.draw.rect(
            surface,
            (12, 19, 26),
            pygame.Rect(0, 0, self._screen_rect.width, self._screen_rect.height),
            width=18,
        )

    def _draw_background_overlays(self, surface: pygame.Surface) -> None:
        screen_size = surface.get_size()

        dark_layer = pygame.Surface(screen_size, pygame.SRCALPHA)
        dark_layer.fill((0, 0, 0, 68))
        surface.blit(dark_layer, (0, 0))

        top_layer = pygame.Surface((screen_size[0], 170), pygame.SRCALPHA)
        top_layer.fill((6, 10, 18, 92))
        surface.blit(top_layer, (0, 0))

        bottom_layer = pygame.Surface((screen_size[0], 150), pygame.SRCALPHA)
        bottom_layer.fill((0, 0, 0, 92))
        surface.blit(bottom_layer, (0, screen_size[1] - 150))

        side = max(80, screen_size[0] // 7)
        left_layer = pygame.Surface((side, screen_size[1]), pygame.SRCALPHA)
        left_layer.fill((0, 0, 0, 58))
        right_layer = pygame.Surface((side, screen_size[1]), pygame.SRCALPHA)
        right_layer.fill((0, 0, 0, 58))
        surface.blit(left_layer, (0, 0))
        surface.blit(right_layer, (screen_size[0] - side, 0))

    def _draw_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        fill: tuple[int, int, int, int] = (15, 24, 29, 192),
        border: tuple[int, int, int, int] = (218, 164, 80, 215),
        radius: int = 20,
        border_width: int = 3,
        shadow: bool = True,
    ) -> None:
        if shadow:
            shadow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                shadow_surface,
                (0, 0, 0, 98),
                shadow_surface.get_rect(),
                border_radius=radius,
            )
            surface.blit(shadow_surface, rect.move(0, 7).topleft)

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel_rect = panel.get_rect()
        pygame.draw.rect(panel, fill, panel_rect, border_radius=radius)
        pygame.draw.rect(
            panel,
            (255, 222, 139, 54),
            panel_rect.inflate(-8, -8),
            width=1,
            border_radius=max(1, radius - 6),
        )
        pygame.draw.rect(
            panel,
            border,
            panel_rect,
            width=border_width,
            border_radius=radius,
        )
        pygame.draw.line(
            panel,
            (255, 244, 176, 82),
            (radius + 6, 7),
            (rect.width - radius - 6, 7),
            2,
        )
        surface.blit(panel, rect.topleft)

    def _draw_title_bar(self, surface: pygame.Surface) -> None:
        width = min(650, self._screen_rect.width - 84)
        title_rect = pygame.Rect(0, 28, width, 82)
        title_rect.centerx = self._screen_rect.centerx
        self._draw_panel(
            surface,
            title_rect,
            fill=(23, 29, 36, 178),
            border=(232, 182, 88, 210),
            radius=22,
            border_width=3,
        )
        draw_centered_text(
            surface,
            "TOWER DEFENSE",
            self._fonts.title,
            (255, 231, 159),
            pygame.Rect(title_rect.x, title_rect.y + 14, title_rect.width, 40),
        )
        draw_centered_text(
            surface,
            "защити королевство от слаймов",
            self._fonts.small,
            (201, 216, 205),
            pygame.Rect(title_rect.x, title_rect.y + 50, title_rect.width, 24),
        )
        left = title_rect.x + 34
        right = title_rect.right - 34
        y = title_rect.centery
        pygame.draw.line(surface, (218, 164, 80), (left, y), (left + 92, y), 2)
        pygame.draw.line(surface, (218, 164, 80), (right - 92, y), (right, y), 2)
        pygame.draw.circle(surface, (244, 204, 110), (left + 106, y), 4)
        pygame.draw.circle(surface, (244, 204, 110), (right - 106, y), 4)

    def _draw_screen_heading(self, surface: pygame.Surface, title: str) -> None:
        heading_rect = pygame.Rect(0, 136, self._screen_rect.width, 32)
        draw_centered_text(
            surface,
            title,
            self._fonts.section,
            (242, 224, 170),
            heading_rect,
        )

    def _draw_button_group_panel(self, surface: pygame.Surface) -> None:
        buttons = self._buttons_for_current_screen()
        if not buttons:
            return
        rect = buttons[0].rect.copy()
        for button in buttons[1:]:
            rect.union_ip(button.rect)
        rect.inflate_ip(78, 70)
        self._draw_panel(
            surface,
            rect,
            fill=(12, 20, 25, 174),
            border=(152, 101, 54, 175),
            radius=24,
            border_width=2,
        )

    def _draw_home(self, surface: pygame.Surface) -> None:
        self._draw_screen_heading(surface, "ГЛАВНОЕ МЕНЮ")
        self._draw_button_group_panel(surface)
        self._draw_buttons(surface)
        self._draw_footer(surface, "ENTER: выбрать    ESC: выход")

    def _draw_modes(self, surface: pygame.Surface) -> None:
        self._draw_screen_heading(surface, "ВЫБЕРИТЕ РЕЖИМ")
        self._draw_button_group_panel(surface)
        self._draw_buttons(surface)
        self._draw_footer(surface, "ESC: назад")

    def _draw_level_select(self, surface: pygame.Surface) -> None:
        self._draw_screen_heading(surface, "ОБЫЧНЫЙ РЕЖИМ — ВЫБОР КАРТЫ")
        cards = self._card_rects()
        if cards:
            panel = cards[0].copy()
            for rect in cards[1:]:
                panel.union_ip(rect)
            panel.inflate_ip(42, 46)
            self._draw_panel(
                surface,
                panel,
                fill=(10, 18, 24, 160),
                border=(148, 100, 52, 164),
                radius=24,
                border_width=2,
            )
        for option, card_rect in zip(
            self._options,
            cards,
            strict=True,
        ):
            self._draw_map_card(surface, option, card_rect)
        self._draw_button_group_panel(surface)
        self._draw_buttons(surface)
        self._draw_footer(surface, "← →: карта    ENTER: начать    ESC: назад")

    def _draw_settings(self, surface: pygame.Surface) -> None:
        self._draw_screen_heading(surface, "НАСТРОЙКИ")
        self._draw_settings_table(surface)
        self._draw_button_group_panel(surface)
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
        panel = pygame.Rect(0, 0, min(640, content.width - 80), 190)
        panel.center = (content.centerx, content.centery + 22)
        self._draw_panel(
            surface,
            panel,
            fill=(12, 20, 25, 188),
            border=(218, 164, 80, 205),
            radius=24,
        )
        draw_centered_text(
            surface,
            title,
            self._fonts.section,
            (255, 231, 159),
            pygame.Rect(panel.x, panel.y + 34, panel.width, 34),
        )
        draw_centered_text(
            surface,
            message,
            self._fonts.body,
            (207, 221, 210),
            pygame.Rect(panel.x + 22, panel.y + 86, panel.width - 44, 34),
        )
        self._draw_button_group_panel(surface)
        self._draw_buttons(surface)
        self._draw_footer(surface, "ESC: назад")

    def _draw_settings_table(self, surface: pygame.Surface) -> None:
        table = self._settings_table_rect()
        self._draw_panel(
            surface,
            table.inflate(48, 42),
            fill=(12, 19, 25, 202),
            border=(218, 164, 80, 196),
            radius=24,
            border_width=3,
        )
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
        row_rect = pygame.Rect(
            table.x - 12,
            self._settings_row_y(row_index) - 5,
            table.width + 24,
            58,
        )
        row_fill = (255, 222, 139, 20) if row_index % 2 == 0 else (0, 0, 0, 24)
        row_surface = pygame.Surface(row_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(row_surface, row_fill, row_surface.get_rect(), border_radius=14)
        surface.blit(row_surface, row_rect.topleft)

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
            separator_y = table.y + 66 + row_index * self._settings_row_gap()
            pygame.draw.line(
                surface,
                (124, 91, 55),
                (table.x - 8, separator_y),
                (table.right + 8, separator_y),
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
        fill = (73, 117, 74) if enabled else (64, 59, 58)
        if is_hovered:
            fill = (91, 139, 87) if enabled else (83, 73, 68)
        border = (231, 190, 105) if is_hovered else (156, 109, 61)
        text = "ВКЛ" if enabled else "ВЫКЛ"

        pygame.draw.rect(surface, (0, 0, 0), rect.move(0, 4), border_radius=17)
        pygame.draw.rect(surface, fill, rect, border_radius=17)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=17)
        knob_x = rect.right - 21 if enabled else rect.x + 21
        pygame.draw.circle(surface, (249, 226, 156), (knob_x, rect.centery), 12)
        draw_centered_text(
            surface,
            text,
            self._fonts.small,
            (255, 246, 213),
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
        fill_width = round(rect.width * volume / 100)
        handle_x = rect.x + fill_width

        track_rect = pygame.Rect(rect.x, rect.centery - 5, rect.width, 10)
        fill_rect = pygame.Rect(rect.x, rect.centery - 5, fill_width, 10)
        track_color = (36, 42, 46) if enabled else (31, 34, 37)
        fill_color = (106, 164, 92) if enabled else (75, 88, 80)
        handle_border = (255, 226, 145) if is_hovered else (163, 118, 66)

        pygame.draw.rect(surface, track_color, track_rect, border_radius=5)
        if fill_width > 0:
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=5)
        pygame.draw.rect(surface, (132, 92, 55), track_rect, width=1, border_radius=5)
        pygame.draw.circle(surface, (0, 0, 0), (handle_x, rect.centery + 3), 13)
        pygame.draw.circle(surface, handle_border, (handle_x, rect.centery), 13)
        pygame.draw.circle(surface, fill_color, (handle_x, rect.centery), 8)

    def _draw_map_card(
        self,
        surface: pygame.Surface,
        option: MapMenuOption,
        rect: pygame.Rect,
    ) -> None:
        is_selected = option.level_number == self._selected_level
        is_hovered = option.level_number == self._hovered_level
        if is_selected:
            fill = (36, 69, 49, 216)
            border = (250, 222, 132, 235)
            border_width = 4
        elif is_hovered:
            fill = (51, 62, 64, 212)
            border = (237, 187, 92, 218)
            border_width = 3
        else:
            fill = (21, 31, 36, 196)
            border = (129, 91, 55, 190)
            border_width = 2

        self._draw_panel(
            surface,
            rect,
            fill=fill,
            border=border,
            radius=18,
            border_width=border_width,
        )

        preview_rect = pygame.Rect(
            rect.x + 16,
            rect.y + 16,
            rect.width - 32,
            min(188, rect.height - 128),
        )
        self._draw_panel(
            surface,
            preview_rect,
            fill=(5, 9, 12, 185),
            border=(107, 77, 51, 180),
            radius=10,
            border_width=2,
            shadow=False,
        )
        preview = self._preview_for(option, preview_rect.size)
        surface.blit(preview, preview.get_rect(center=preview_rect.center))

        draw_centered_text(
            surface,
            option.title,
            self._fonts.section,
            (255, 231, 159),
            pygame.Rect(rect.x, preview_rect.bottom + 14, rect.width, 30),
        )
        status = "ВЫБРАНО" if is_selected else "НАЖМИТЕ, ЧТОБЫ ВЫБРАТЬ"
        status_color: Color = (
            (213, 241, 187) if is_selected else (199, 208, 204)
        )
        draw_centered_text(
            surface,
            status,
            self._fonts.small,
            status_color,
            pygame.Rect(rect.x, preview_rect.bottom + 51, rect.width, 24),
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
        rect = button.rect
        fill: Color = (47, 38, 33)
        border: Color = (169, 112, 58)
        text_color: Color = (246, 232, 190)
        border_width = 2
        if is_focused or is_hovered:
            fill = (73, 52, 39)
            border = (249, 205, 116)
            text_color = (255, 244, 199)
            border_width = 3
        if button.key == "start":
            fill = (72, 118, 70) if not is_hovered else (91, 147, 82)
            border = (246, 224, 144)
            text_color = (255, 252, 230)
            border_width = 3

        pygame.draw.rect(surface, (0, 0, 0), rect.move(0, 6), border_radius=10)
        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(
            surface,
            (31, 22, 18),
            rect.inflate(-8, -8),
            width=1,
            border_radius=7,
        )
        pygame.draw.rect(
            surface,
            border,
            rect,
            width=border_width,
            border_radius=10,
        )
        pygame.draw.line(
            surface,
            (255, 232, 154),
            (rect.x + 18, rect.y + 7),
            (rect.right - 18, rect.y + 7),
            1,
        )
        diamond_y = rect.centery
        for x in (rect.x + 24, rect.right - 24):
            pygame.draw.polygon(
                surface,
                border,
                ((x, diamond_y - 5), (x + 5, diamond_y), (x, diamond_y + 5), (x - 5, diamond_y)),
            )
        draw_centered_text(
            surface,
            button.title,
            self._fonts.section,
            text_color,
            rect,
        )

    def _draw_footer(self, surface: pygame.Surface, text: str) -> None:
        if not self._settings.show_menu_hints:
            return
        rendered = self._fonts.small.render(text, True, (216, 226, 216))
        footer_rect = pygame.Rect(
            0,
            self._screen_rect.bottom - 54,
            min(self._screen_rect.width - 80, rendered.get_width() + 76),
            34,
        )
        footer_rect.centerx = self._screen_rect.centerx
        self._draw_panel(
            surface,
            footer_rect,
            fill=(9, 15, 20, 142),
            border=(132, 91, 55, 150),
            radius=17,
            border_width=1,
            shadow=False,
        )
        surface.blit(rendered, rendered.get_rect(center=footer_rect.center))

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
        width = min(430, self._screen_rect.width - 72)
        height = 60
        gap = 18
        total_height = height * len(descriptions) + gap * (len(descriptions) - 1)
        top = self._screen_rect.centery - total_height // 2 + 58
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
        width = min(400, self._screen_rect.width - 72)
        height = 52
        gap = 14
        total_height = height * len(descriptions) + gap * (len(descriptions) - 1)
        top = self._screen_rect.bottom - 52 - total_height
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
                    min(table.bottom + 92, self._screen_rect.bottom - 96),
                    width,
                    height,
                ),
            ),
        )

    def _settings_table_rect(self) -> pygame.Rect:
        width = min(820, self._screen_rect.width - 96)
        height = 238
        rect = pygame.Rect(0, 0, width, height)
        rect.centerx = self._screen_rect.centerx
        rect.y = min(
            210,
            max(176, self._screen_rect.height - height - 170),
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
        horizontal_gap = 26
        outer_margin = 54
        max_width = min(1120, self._screen_rect.width - outer_margin * 2)
        card_width = (max_width - horizontal_gap * (count - 1)) // count
        card_height = min(270, max(180, self._screen_rect.height - 455))
        total_width = card_width * count + horizontal_gap * (count - 1)
        left = (self._screen_rect.width - total_width) // 2
        top = 200 if self._screen_rect.height >= 680 else 190
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
