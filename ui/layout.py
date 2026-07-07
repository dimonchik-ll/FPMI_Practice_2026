from __future__ import annotations

from dataclasses import dataclass

import pygame

PANEL_WIDTH = 320


@dataclass(frozen=True, slots=True)
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

    @property
    def panel(self) -> pygame.Rect:
        return pygame.Rect(self.map_width, 0, PANEL_WIDTH, self.height)

    @property
    def window_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.map_width + PANEL_WIDTH, self.height)

    @property
    def content_width(self) -> int:
        return PANEL_WIDTH - self.margin * 2

    @property
    def title_position(self) -> tuple[int, int]:
        return self.map_width + self.margin, 12

    @property
    def status_badge_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.map_width + self.margin,
            50,
            self.content_width,
            25,
        )

    @property
    def pause_button(self) -> pygame.Rect:
        return pygame.Rect(
            self.map_width + self.margin,
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
            self.map_width + self.margin,
            self.height - self.margin - self.start_button_height,
            self.content_width,
            self.start_button_height,
        )

    @property
    def map_stats_panel(self) -> pygame.Rect:
        return pygame.Rect(0, 0, min(self.map_width, 328), 36)

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
            self.map_width + self.margin,
            self.side_content_top,
        )

    @property
    def tower_list_viewport(self) -> pygame.Rect:
        height = (
                self.visible_tower_count * self.tower_card_height
                + (self.visible_tower_count - 1) * self.gap
        )

        return pygame.Rect(
            self.map_width + self.margin,
            self.side_content_top + self.tower_list_heading_height + self.gap,
            self.content_width,
            height,
        )

    def tower_info_area(self) -> pygame.Rect:
        top = self.tower_list_viewport.bottom + self.gap
        bottom = self.start_wave_button.top - self.gap

        return pygame.Rect(
            self.map_width + self.margin,
            top,
            self.content_width,
            max(0, bottom - top),
        )
