from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pygame

from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import draw_centered_text


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


class MainMenu:
    """Стартовый экран: выбор карты и запуск выбранного уровня."""

    def __init__(
        self,
        screen_size: tuple[int, int],
        options: tuple[MapMenuOption, ...],
    ) -> None:
        if not options:
            raise ValueError("Для главного меню нужна хотя бы одна карта.")

        self._screen_rect = pygame.Rect((0, 0), screen_size)
        self._options = options
        self._theme = UiTheme()
        self._fonts = UiFonts()

        self._selected_level = options[0].level_number
        self._hovered_level: int | None = None
        self._start_hovered = False
        self._preview_cache: dict[tuple[int, int, int], pygame.Surface] = {}

    @property
    def selected_level(self) -> int:
        return self._selected_level

    def handle_event(self, event: pygame.event.Event) -> MainMenuAction | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return MainMenuAction(MainMenuActionKind.QUIT)

            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return MainMenuAction(
                    MainMenuActionKind.START_GAME,
                    self._selected_level,
                )

            if event.key in (pygame.K_LEFT, pygame.K_UP):
                self._move_selection(-1)
                return None

            if event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self._move_selection(1)
                return None

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        self._update_hover(event.pos)

        if self._hovered_level is not None:
            self._selected_level = self._hovered_level
            return None

        if self._start_hovered:
            return MainMenuAction(
                MainMenuActionKind.START_GAME,
                self._selected_level,
            )

        return None

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_background(surface)
        self._update_hover(pygame.mouse.get_pos())

        draw_centered_text(
            surface,
            "TOWER DEFENSE",
            self._fonts.title,
            self._theme.title_text,
            pygame.Rect(0, 42, self._screen_rect.width, 42),
        )
        draw_centered_text(
            surface,
            "ВЫБЕРИТЕ КАРТУ",
            self._fonts.section,
            self._theme.muted_text,
            pygame.Rect(0, 94, self._screen_rect.width, 30),
        )

        for option, card_rect in zip(self._options, self._card_rects(), strict=True):
            self._draw_map_card(surface, option, card_rect)

        start_rect = self._start_button_rect()
        self._draw_start_button(surface, start_rect)

        draw_centered_text(
            surface,
            "← →: выбор карты    ENTER: начать    ESC: выход",
            self._fonts.small,
            self._theme.muted_text,
            pygame.Rect(0, self._screen_rect.bottom - 40, self._screen_rect.width, 24),
        )

    def _draw_background(self, surface: pygame.Surface) -> None:
        surface.fill((12, 21, 28))

        pygame.draw.rect(
            surface,
            (18, 33, 43),
            pygame.Rect(0, 0, self._screen_rect.width, 144),
        )
        pygame.draw.line(
            surface,
            self._theme.panel_border,
            (0, 144),
            (self._screen_rect.width, 144),
            2,
        )

        accent_color: Color = (35, 65, 58)
        pygame.draw.circle(
            surface,
            accent_color,
            (self._screen_rect.width - 80, 60),
            160,
        )
        pygame.draw.circle(
            surface,
            (29, 51, 67),
            (72, self._screen_rect.height - 40),
            150,
        )

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
        status_color: Color = (210, 238, 185) if is_selected else self._theme.muted_text
        draw_centered_text(
            surface,
            status,
            self._fonts.small,
            status_color,
            pygame.Rect(rect.x, preview_rect.bottom + 48, rect.width, 24),
        )

    def _draw_start_button(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        fill: Color = (73, 130, 82)
        border: Color = (196, 232, 179)

        if self._start_hovered:
            fill = (91, 150, 97)

        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, border, rect, width=3, border_radius=10)
        draw_centered_text(
            surface,
            "НАЧАТЬ ИГРУ",
            self._fonts.section,
            (250, 250, 243),
            rect,
        )

    def _card_rects(self) -> tuple[pygame.Rect, ...]:
        count = len(self._options)
        horizontal_gap = 24
        outer_margin = 48
        max_width = min(1100, self._screen_rect.width - outer_margin * 2)
        card_width = (max_width - horizontal_gap * (count - 1)) // count
        card_height = min(330, max(250, self._screen_rect.height - 370))
        total_width = card_width * count + horizontal_gap * (count - 1)
        left = (self._screen_rect.width - total_width) // 2
        top = max(156, (self._screen_rect.height - card_height - 134) // 2)

        return tuple(
            pygame.Rect(
                left + index * (card_width + horizontal_gap),
                top,
                card_width,
                card_height,
            )
            for index in range(count)
        )

    def _start_button_rect(self) -> pygame.Rect:
        width = min(380, self._screen_rect.width - 64)
        rect = pygame.Rect(0, self._screen_rect.bottom - 108, width, 54)
        rect.centerx = self._screen_rect.centerx
        return rect

    def _update_hover(self, position: tuple[int, int]) -> None:
        self._hovered_level = None

        for option, rect in zip(self._options, self._card_rects(), strict=True):
            if rect.collidepoint(position):
                self._hovered_level = option.level_number
                break

        self._start_hovered = self._start_button_rect().collidepoint(position)

    def _move_selection(self, direction: int) -> None:
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
        canvas.blit(scaled, scaled.get_rect(center=(target_width // 2, target_height // 2)))
        self._preview_cache[cache_key] = canvas
        return canvas
