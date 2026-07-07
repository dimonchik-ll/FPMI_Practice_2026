from __future__ import annotations

import pygame

from core.game_shell import CoreWorld
from core.map_renderer import MapRenderer
from enemies.api import EnemySystem, WAVE_PLANS
from shared.contracts import GameEventKind, GameSnapshot, TowerKind, UiActionKind, Vector2
from towers.api import TowerSystem
from ui.api import PANEL_WIDTH, UiSystem
from ui.economy import Economy

MAX_WAVES = max(WAVE_PLANS)


class TowerDefenseApp:
    def __init__(self) -> None:
        pygame.init()

        self.core = CoreWorld()
        self.map = self.core.game_map
        self.screen = pygame.display.set_mode(
            (self.map.pixel_width + PANEL_WIDTH, self.map.pixel_height)
        )
        pygame.display.set_caption("Tower Defense — Team Scaffold")

        self.clock = pygame.time.Clock()
        self.renderer = MapRenderer()
        self.ui = UiSystem(self.map.pixel_width, self.map.pixel_height)
        self.running = True

        self._reset_game_state()

    def run(self) -> None:
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(delta_time)
            self._draw()

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            action = self.ui.handle_event(event)
            if action is not None:
                self._handle_ui_action(action.kind, action.payload or {})
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.ui.is_overlay_point(event.pos):
                    continue
                self._try_build(Vector2(float(event.pos[0]), float(event.pos[1])))

    def _handle_ui_action(self, action_kind: UiActionKind, payload: dict) -> None:
        if action_kind == UiActionKind.RESTART:
            self._restart_game()
            return

        if action_kind == UiActionKind.PAUSE:
            if not self._is_game_finished():
                self.paused = True
            return

        if action_kind == UiActionKind.RESUME:
            if not self._is_game_finished():
                self.paused = False
            return

        if self.paused or self._is_game_finished():
            return

        if action_kind == UiActionKind.SELECT_TOWER:
            tower_kind = payload.get("tower_kind")
            if isinstance(tower_kind, TowerKind):
                self.economy.select_tower(tower_kind)
            return

        if action_kind == UiActionKind.START_WAVE:
            if not self.enemies.is_wave_active():
                self.enemies.start_wave(self.wave_number, self.core.route())

    def _try_build(self, position: Vector2) -> None:
        if (
            position.x >= self.map.pixel_width
            or self.paused
            or self._is_game_finished()
        ):
            return

        tower_kind = self.economy.state.selected_tower
        if tower_kind is None or not self.economy.can_buy(tower_kind):
            return

        cell = self.map.world_to_cell(position)
        request = self.core.create_build_request(cell, tower_kind)
        if request is None:
            return

        if not self.core.confirm_build(cell):
            return

        if not self.economy.buy(tower_kind):
            self.core.cancel_build(cell)
            return

        self.towers.build(request)

    def _update(self, delta_time: float) -> None:
        if self.paused or self._is_game_finished():
            return

        damage_commands = self.towers.update(delta_time, self.enemies.views())
        events = self.enemies.apply_damage(damage_commands)
        events.extend(self.enemies.update(delta_time))

        for event in events:
            if event.kind == GameEventKind.ENEMY_DEFEATED:
                self.economy.add_reward(int(event.payload["reward"]))
            elif event.kind == GameEventKind.ENEMY_REACHED_GOAL:
                self.economy.take_base_damage(int(event.payload["damage"]))
            elif event.kind == GameEventKind.WAVE_COMPLETED:
                if self.wave_number >= MAX_WAVES:
                    self.victory = True
                else:
                    self.wave_number += 1

    def _draw(self) -> None:
        self.screen.fill((20, 30, 25))
        self.renderer.draw(self.screen, self.map)
        self.enemies.draw(self.screen)
        self.towers.draw(self.screen)

        snapshot = GameSnapshot(
            player=self.economy.state.to_view(),
            wave_number=self.wave_number,
            enemies=self.enemies.views(),
            towers=self.towers.views(),
            wave_is_active=self.enemies.is_wave_active(),
            game_over=self.economy.is_game_over(),
            victory=self.victory,
            paused=self.paused,
        )
        self.ui.draw(self.screen, snapshot)
        pygame.display.flip()

    def _restart_game(self) -> None:
        self.core = CoreWorld()
        self.map = self.core.game_map

        expected_size = (self.map.pixel_width + PANEL_WIDTH, self.map.pixel_height)
        if self.screen.get_size() != expected_size:
            self.screen = pygame.display.set_mode(expected_size)
            self.ui = UiSystem(self.map.pixel_width, self.map.pixel_height)

        self._reset_game_state()

    def _reset_game_state(self) -> None:
        self.towers = TowerSystem()
        self.enemies = EnemySystem()
        self.economy = Economy()
        self.wave_number = 1
        self.victory = False
        self.paused = False

    def _is_game_finished(self) -> bool:
        return self.economy.is_game_over() or self.victory


def run() -> None:
    TowerDefenseApp().run()
