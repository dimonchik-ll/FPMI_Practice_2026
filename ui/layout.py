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
    tower_card_height: int = 48
    visible_tower_count: int = 3
    start_button_height: int = 40

    @property
    def panel(self) -> pygame.Rect:
        return pygame.Rect(self.map_width, 0, PANEL_WIDTH, self.height)

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
    def side_content_top(self) -> int:
        return self.status_badge_rect.bottom + self.gap

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
        available_width = max(0, self.map_width - self.margin * 2)
        width = min(254, available_width)

        return pygame.Rect(
            self.margin,
            self.margin,
            width,
            76,
        )

    def map_stat_card_rect(self, index: int) -> pygame.Rect:
        panel = self.map_stats_panel
        inner_margin = 7
        inner_width = panel.width - inner_margin * 2
        card_width = (inner_width - self.gap) // 2
        card_height = 27

        row, column = divmod(index, 2)

        return pygame.Rect(
            panel.x + inner_margin + column * (card_width + self.gap),
            panel.y + inner_margin + row * (card_height + self.gap),
            card_width,
            card_height,
        )

    @property
    def tower_list_viewport(self) -> pygame.Rect:
        height = (
            self.visible_tower_count * self.tower_card_height
            + (self.visible_tower_count - 1) * self.gap
        )

        return pygame.Rect(
            self.map_width + self.margin,
            self.start_wave_button.top - self.gap - height,
            self.content_width,
            height,
        )

    def tower_info_area(self) -> pygame.Rect:
        top = self.side_content_top
        bottom = self.tower_list_viewport.top - self.gap

        return pygame.Rect(
            self.map_width + self.margin,
            top,
            self.content_width,
            max(0, bottom - top),
        )