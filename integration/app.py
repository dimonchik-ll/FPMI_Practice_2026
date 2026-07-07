from __future__ import annotations

import pygame

from core.game_shell import CoreWorld
from core.map_renderer import MapRenderer
from enemies.api import EnemySystem, WAVE_PLANS
from shared.contracts import (
    GameEventKind,
    GameSnapshot,
    TowerKind,
    UiActionKind,
    Vector2,
)
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
        self.towers = TowerSystem()
        self.enemies = EnemySystem()
        self.economy = Economy()
        self.ui = UiSystem(self.map.pixel_width, self.map.pixel_height)
        self.wave_number = 1
        self.victory = False
        self.running = True

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

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.ui.is_overlay_point(event.pos)
            ):
                continue

            action = self.ui.handle_event(event)
            if action is not None:
                self._handle_ui_action(action.kind, action.payload or {})
                continue

            if event.type != pygame.MOUSEBUTTONDOWN:
                continue

            position = Vector2(float(event.pos[0]), float(event.pos[1]))
            if event.button == 1:
                self._try_build(position)
            elif event.button == 3:
                self._try_remove_tower(position)

    def _handle_ui_action(self, action_kind: UiActionKind, payload: dict) -> None:
        if action_kind == UiActionKind.SELECT_TOWER:
            tower_kind = payload.get("tower_kind")
            if isinstance(tower_kind, TowerKind):
                self.economy.select_tower(tower_kind)
        elif action_kind == UiActionKind.START_WAVE:
            if not self.enemies.is_wave_active() and not self.victory:
                self.enemies.start_wave(self.wave_number, self.core.route())

    def _try_build(self, position: Vector2) -> None:
        if (
            position.x >= self.map.pixel_width
            or self.economy.is_game_over()
            or self.victory
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

    def _try_remove_tower(self, position: Vector2) -> None:
        """Удаляет башню правой кнопкой мыши и освобождает её build zone.

        TowerSystem отвечает только за башню и её снаряды. Занятость клеток
        является состоянием карты, поэтому освобождение выполняется через
        CoreWorld после успешного удаления башни.
        """
        if (
            position.x < 0
            or position.y < 0
            or position.x >= self.map.pixel_width
            or position.y >= self.map.pixel_height
            or self.economy.is_game_over()
            or self.victory
        ):
            return

        removed_tower = self.towers.remove_at_position(position)
        if removed_tower is None:
            return

        self.core.release_tower_cell(removed_tower.cell)

    def _update(self, delta_time: float) -> None:
        if self.economy.is_game_over() or self.victory:
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
        )
        self.ui.draw(self.screen, snapshot)
        self._draw_end_state(snapshot)
        pygame.display.flip()

    def _draw_end_state(self, snapshot: GameSnapshot) -> None:
        message = (
            "ПОБЕДА"
            if snapshot.victory
            else "ИГРА ОКОНЧЕНА"
            if snapshot.game_over
            else None
        )
        if message is None:
            return

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        font = pygame.font.Font(None, 74)
        text = font.render(message, True, (248, 236, 174))
        self.screen.blit(text, text.get_rect(center=self.screen.get_rect().center))


def run() -> None:
    TowerDefenseApp().run()
