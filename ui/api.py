from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot, UiAction
from ui.game_stats import GameStatsPanel
from ui.hud import HudPanel
from ui.layout import PANEL_WIDTH, UiLayout
from ui.theme import UiFonts, UiTheme
from ui.tower_menu import TowerMenu
from ui.wave_control import WaveControl
from ui.widgets import UiComponent

__all__ = ["PANEL_WIDTH", "UiSystem"]


class UiSystem:
    def __init__(self, map_width: int, height: int) -> None:
        layout = UiLayout(map_width, height)
        theme = UiTheme()
        fonts = UiFonts()

        self._snapshot: GameSnapshot | None = None
        self._game_stats = GameStatsPanel(layout, theme, fonts)

        self._components: tuple[UiComponent, ...] = (
            HudPanel(layout, theme, fonts),
            self._game_stats,
            TowerMenu(layout, theme, fonts),
            WaveControl(layout, theme, fonts),
        )

    def handle_event(self, event: pygame.event.Event) -> UiAction | None:
        for component in reversed(self._components):
            action = component.handle_event(event, self._snapshot)

            if action is not None:
                return action

        return None

    def is_overlay_point(self, position: tuple[int, int]) -> bool:
        return self._game_stats.contains_point(position)

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self._snapshot = snapshot

        for component in self._components:
            component.draw(surface, snapshot)