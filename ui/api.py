from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot, UiAction, UiActionKind
from ui.game_stats import GameStatsPanel
from ui.hud import HudPanel
from ui.layout import PANEL_WIDTH, UiLayout
from ui.overlays import EndGameOverlay, PauseOverlay
from ui.pause_control import PauseControl
from ui.theme import UiFonts, UiTheme
from ui.tower_action_menu import TowerActionMenu
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
        self._tower_action_menu = TowerActionMenu(layout, theme, fonts)
        self._components: tuple[UiComponent, ...] = (
            HudPanel(layout, theme, fonts),
            self._game_stats,
            TowerMenu(layout, theme, fonts),
            WaveControl(layout, theme, fonts),
            PauseControl(layout, theme, fonts),
        )

    def open_tower_menu(self, tower_identifier: str) -> None:
        self._tower_action_menu.open(tower_identifier)

    def close_tower_menu(self) -> None:
        self._tower_action_menu.close()

    def handle_event(self, event: pygame.event.Event) -> UiAction | None:
        snapshot = self._snapshot
        if snapshot is None:
            return None

        if snapshot.game_over or snapshot.victory:
            self.close_tower_menu()
            return self._end_game_overlay.handle_event(event, snapshot)

        if snapshot.paused:
            self.close_tower_menu()
            return self._pause_overlay.handle_event(event, snapshot)

        tower_menu_action = self._tower_action_menu.handle_event(event, snapshot)
        if tower_menu_action is not None:
            if tower_menu_action.kind == UiActionKind.CLOSE_TOWER_MENU:
                self.close_tower_menu()

            return tower_menu_action

        if self._tower_action_menu.is_open and event.type in (
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION,
            pygame.MOUSEWHEEL,
        ):
            return None

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

        return (
            self._game_stats.contains_point(position)
            or self._tower_action_menu.contains_point(position)
        )

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self._snapshot = snapshot
        self._tower_action_menu.sync(snapshot)

        for component in self._components:
            component.draw(surface, snapshot)

        if snapshot.game_over or snapshot.victory:
            self._end_game_overlay.draw(surface, snapshot)
        elif snapshot.paused:
            self._pause_overlay.draw(surface, snapshot)
        else:
            self._tower_action_menu.draw(surface, snapshot)
