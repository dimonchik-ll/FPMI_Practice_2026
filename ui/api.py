from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot, UiAction, UiActionKind
from ui.game_stats import GameStatsPanel
from ui.hud import HudPanel
from ui.layout import PANEL_WIDTH, UiLayout
from ui.overlays import EndGameOverlay, PauseOverlay
from ui.pause_control import PauseControl
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
        self._pause_overlay = PauseOverlay(layout, theme, fonts)
        self._end_game_overlay = EndGameOverlay(layout, theme, fonts)
        self._components: tuple[UiComponent, ...] = (
            HudPanel(layout, theme, fonts),
            self._game_stats,
            TowerMenu(layout, theme, fonts),
            WaveControl(layout, theme, fonts),
            PauseControl(layout, theme, fonts),
        )

    def handle_event(self, event: pygame.event.Event) -> UiAction | None:
        snapshot = self._snapshot
        if snapshot is None:
            return None

        if snapshot.game_over or snapshot.victory:
            return self._end_game_overlay.handle_event(event, snapshot)

        if snapshot.paused:
            return self._pause_overlay.handle_event(event, snapshot)

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
            return UiAction(UiActionKind.PAUSE)

        for component in reversed(self._components):
            action = component.handle_event(event, snapshot)
            if action is not None:
                return action
        return None

    def is_overlay_point(self, position: tuple[int, int]) -> bool:
        snapshot = self._snapshot
        if snapshot is not None and (
            snapshot.paused or snapshot.game_over or snapshot.victory
        ):
            return True
        return self._game_stats.contains_point(position)

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self._snapshot = snapshot
        for component in self._components:
            component.draw(surface, snapshot)

        if snapshot.game_over or snapshot.victory:
            self._end_game_overlay.draw(surface, snapshot)
        elif snapshot.paused:
            self._pause_overlay.draw(surface, snapshot)
