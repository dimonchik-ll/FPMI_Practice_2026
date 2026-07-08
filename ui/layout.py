from __future__ import annotations

from dataclasses import dataclass, field

import pygame

PANEL_WIDTH = 320
HUD_TOGGLE_WIDTH = 38
HUD_TOGGLE_HEIGHT = 58
HUD_SLIDE_SPEED = 900.0


@dataclass(slots=True)
class UiLayout:
    map_width: int
    height: int
    margin: int = 14
    gap: int = 8
    tower_list_heading_height: int = 30
    tower_card_height: int = 48
    visible_tower_count: int = 3
    pause_button_height: int = 34
    start_button_height: int = 40
    stats_panel_width: int = 400
    stats_panel_height: int = 35
    hud_open: bool = True
    panel_x: float = field(init=False)

    def __post_init__(self) -> None:
        self.panel_x = float(self.open_panel_x)

    @property
    def open_panel_x(self) -> int:
        return max(0, self.map_width - PANEL_WIDTH)

    @property
    def closed_panel_x(self) -> int:
        return self.map_width

    @property
    def hud_target_x(self) -> int:
        return self.open_panel_x if self.hud_open else self.closed_panel_x

    @property
    def panel_left(self) -> int:
        return int(round(self.panel_x))

    @property
    def panel(self) -> pygame.Rect:
        return pygame.Rect(self.panel_left, 0, PANEL_WIDTH, self.height)

    @property
    def visible_panel(self) -> pygame.Rect:
        return self.panel.clip(self.window_rect)

    @property
    def window_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.map_width, self.height)

    @property
    def hud_toggle_button(self) -> pygame.Rect:
        x = self.panel_left - HUD_TOGGLE_WIDTH
        x = max(0, min(x, self.map_width - HUD_TOGGLE_WIDTH))
        return pygame.Rect(x, 18, HUD_TOGGLE_WIDTH, HUD_TOGGLE_HEIGHT)

    @property
    def content_width(self) -> int:
        return PANEL_WIDTH - self.margin * 2

    @property
    def title_position(self) -> tuple[int, int]:
        return self.panel_left + self.margin, 12

    @property
    def status_badge_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.panel_left + self.margin,
            50,
            self.content_width,
            25,
        )

    @property
    def pause_button(self) -> pygame.Rect:
        return pygame.Rect(
            self.panel_left + self.margin,
            self.status_badge_rect.bottom + self.gap,
            self.content_width,
            self.pause_button_height,
        )

    @property
    def side_content_top(self) -> int:
        return self.pause_button.bottom + self.gap

    @property
    def start_wave_button(self) -> pygame.Rect:
        return pygame.Rect(
            self.panel_left + self.margin,
            self.height - self.margin - self.start_button_height,
            self.content_width,
            self.start_button_height,
        )

    @property
    def map_stats_panel(self) -> pygame.Rect:
        return pygame.Rect(
            0,
            0,
            min(self.map_width, self.stats_panel_width),
            self.stats_panel_height,
        )

    def map_stat_card_rect(self, index: int) -> pygame.Rect:
        panel = self.map_stats_panel
        stat_count = 4
        cell_width = panel.width // stat_count
        x = panel.x + index * cell_width
        width = panel.right - x if index == stat_count - 1 else cell_width
        return pygame.Rect(x, panel.y, width, panel.height)

    @property
    def tower_list_heading_position(self) -> tuple[int, int]:
        return (
            self.panel_left + self.margin,
            self.side_content_top,
        )

    @property
    def tower_list_viewport(self) -> pygame.Rect:
        height = (
            self.visible_tower_count * self.tower_card_height
            + (self.visible_tower_count - 1) * self.gap
        )
        return pygame.Rect(
            self.panel_left + self.margin,
            self.side_content_top + self.tower_list_heading_height + self.gap,
            self.content_width,
            height,
        )

    def tower_info_area(self) -> pygame.Rect:
        top = self.tower_list_viewport.bottom + self.gap
        bottom = self.start_wave_button.top - self.gap
        return pygame.Rect(
            self.panel_left + self.margin,
            top,
            self.content_width,
            max(0, bottom - top),
        )

    def hud_contains_point(self, position: tuple[int, int]) -> bool:
        return (
            self.visible_panel.collidepoint(position)
            or self.hud_toggle_button.collidepoint(position)
        )
