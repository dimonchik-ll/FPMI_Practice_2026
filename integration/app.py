from __future__ import annotations

import pygame

from core.game_shell import CoreWorld
from core.levels import LEVEL_PATHS
from core.map_model import GameMap
from core.map_renderer import MapRenderer
from enemies.api import EnemySystem
from enemies.tuning import CAMPAIGN_MAX_WAVES
from shared.audio import AudioSystem
from shared.contracts import (
    BUILDABLE_TOWER_KINDS,
    GameEventKind,
    GameSnapshot,
    TowerKind,
    UiActionKind,
    Vector2,
)
from towers.api import TowerSystem
from ui.api import UiSystem
from ui.economy import Economy
from ui.main_menu import MainMenu, MainMenuActionKind, MapMenuOption

# CAMPAIGN_MAX_WAVES перенесён в enemies.tuning
MENU_SIZE = (1280, 720)


class TowerDefenseApp:
    def __init__(self, level_number: int, audio: AudioSystem | None = None) -> None:
        if not pygame.get_init():
            pygame.init()
        self.level_number = level_number
        self.core = self._create_world()
        self.map = self.core.game_map
        self.screen = pygame.display.set_mode(
            (self.map.pixel_width, self.map.pixel_height)
        )
        pygame.display.set_caption(f"Tower Defense — Карта {self.level_number}")
        self.clock = pygame.time.Clock()
        self.audio = audio
        if self.audio is not None:
            self.audio.play_game_music()
        self.renderer = MapRenderer()
        self.towers = TowerSystem(self.audio)
        self.enemies = EnemySystem()
        self.economy = Economy()
        self.ui = UiSystem(self.map.pixel_width, self.map.pixel_height)
        self.wave_number = 1
        self.victory = False
        self.paused = False
        self.running = True
        self.return_to_menu = False

    def run(self) -> bool:
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0
            if self.audio is not None:
                self.audio.refresh_settings()
            self._handle_events()
            self._update(delta_time)
            self._draw()
        return self.return_to_menu

    def _create_world(self) -> CoreWorld:
        game_map = GameMap.create_from_level(self.level_number)
        return CoreWorld(game_map=game_map)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.return_to_menu = False
                self.running = False
                continue

            action = self.ui.handle_event(event)
            if action is not None:
                self._handle_ui_action(action.kind, action.payload or {})
                continue

            if self.paused:
                continue

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and self.ui.is_overlay_point(event.pos)
            ):
                continue

            if event.type != pygame.MOUSEBUTTONDOWN:
                continue

            position = Vector2(float(event.pos[0]), float(event.pos[1]))
            if event.button == 1:
                self._try_build(position)
            elif event.button == 3:
                self._try_open_tower_menu(position)

    def _handle_ui_action(
        self,
        action_kind: UiActionKind,
        payload: dict,
    ) -> None:
        if action_kind == UiActionKind.PAUSE:
            if not self.economy.is_game_over() and not self.victory:
                self.paused = True
            return
        if action_kind == UiActionKind.RESUME:
            if not self.economy.is_game_over() and not self.victory:
                self.paused = False
            return
        if action_kind == UiActionKind.OPEN_MAIN_MENU:
            self.return_to_menu = True
            self.running = False
            return
        if action_kind == UiActionKind.RESTART:
            self._restart_game()
            return
        if action_kind == UiActionKind.SELECT_TOWER:
            if self.paused:
                return
            tower_kind = payload.get("tower_kind")
            if isinstance(tower_kind, TowerKind) and tower_kind in BUILDABLE_TOWER_KINDS:
                self.economy.select_tower(tower_kind)
            return
        if action_kind == UiActionKind.CLOSE_TOWER_MENU:
            self.ui.close_tower_menu()
            return
        if action_kind == UiActionKind.UPGRADE_TOWER:
            tower_identifier = payload.get("tower_id")
            if isinstance(tower_identifier, str):
                self._try_upgrade_tower(tower_identifier)
            return
        if action_kind == UiActionKind.REMOVE_TOWER:
            tower_identifier = payload.get("tower_id")
            if isinstance(tower_identifier, str):
                self._try_remove_tower(tower_identifier)
            return
        if action_kind == UiActionKind.START_WAVE:
            if (
                not self.paused
                and not self.enemies.is_wave_active()
                and not self.victory
                and not self.economy.is_game_over()
            ):
                self.enemies.start_wave(self.wave_number, self.core.route())

    def _restart_game(self) -> None:
        self.core = self._create_world()
        self.map = self.core.game_map
        self.towers = TowerSystem(self.audio)
        self.enemies = EnemySystem()
        self.economy = Economy()
        self.ui = UiSystem(self.map.pixel_width, self.map.pixel_height)
        self.wave_number = 1
        self.victory = False
        self.paused = False

    def _try_build(self, position: Vector2) -> None:
        if (
            position.x >= self.map.pixel_width
            or self.paused
            or self.economy.is_game_over()
            or self.victory
        ):
            return
        tower_kind = self.economy.state.selected_tower
        if (
            tower_kind not in BUILDABLE_TOWER_KINDS
            or not self.economy.can_buy(tower_kind)
        ):
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

    def _try_open_tower_menu(self, position: Vector2) -> None:
        if (
            position.x < 0
            or position.y < 0
            or position.x >= self.map.pixel_width
            or position.y >= self.map.pixel_height
            or self.paused
            or self.economy.is_game_over()
            or self.victory
        ):
            return
        tower = self.towers.tower_at_position(position)
        if tower is None:
            self.ui.close_tower_menu()
            return
        self.ui.open_tower_menu(tower.identifier)

    def _try_upgrade_tower(self, tower_identifier: str) -> None:
        if self.paused or self.economy.is_game_over() or self.victory:
            return
        upgrade_cost = self.towers.upgrade_cost(tower_identifier)
        if upgrade_cost is None or not self.economy.can_afford(upgrade_cost):
            return
        if self.towers.upgrade(tower_identifier):
            self.economy.spend(upgrade_cost)

    def _try_remove_tower(self, tower_identifier: str) -> None:
        if self.paused or self.economy.is_game_over() or self.victory:
            return
        removed_tower = self.towers.remove(tower_identifier)
        if removed_tower is None:
            return
        self.core.release_tower_cell(removed_tower.cell)
        self.ui.close_tower_menu()

    def _update(self, delta_time: float) -> None:
        if self.paused or self.economy.is_game_over() or self.victory:
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
                if self.wave_number >= CAMPAIGN_MAX_WAVES:
                    self.victory = True
                else:
                    self.wave_number += 1

    def _draw(self) -> None:
        self.screen.fill((20, 30, 25))
        self.renderer.draw(self.screen, self.map)
        self.enemies.draw(self.screen)
        self.towers.draw(self.screen)
        # HP bar рисуется отдельным верхним слоем после башен,
        # чтобы башня не перекрывала полоску здоровья врага.
        self.enemies.draw_health_bars(self.screen)
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


def _build_menu_options() -> tuple[MapMenuOption, ...]:
    renderer = MapRenderer()
    options: list[MapMenuOption] = []
    for level_number in sorted(LEVEL_PATHS):
        game_map = GameMap.create_from_level(level_number)
        preview = pygame.Surface((game_map.pixel_width, game_map.pixel_height))
        preview.fill((20, 30, 25))
        renderer.draw(preview, game_map)
        options.append(
            MapMenuOption(
                level_number=level_number,
                title=f"КАРТА {level_number}",
                preview=preview,
            )
        )
    return tuple(options)


def _run_main_menu(audio: AudioSystem | None = None) -> int | None:
    screen = pygame.display.set_mode(MENU_SIZE)
    pygame.display.set_caption("Tower Defense")
    if audio is not None:
        audio.play_menu_music()
    menu = MainMenu(screen.get_size(), _build_menu_options())
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        if audio is not None:
            audio.refresh_settings()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            action = menu.handle_event(event)
            if action is None:
                continue
            if action.kind == MainMenuActionKind.QUIT:
                return None
            if action.kind == MainMenuActionKind.START_GAME:
                return action.level_number
        menu.draw(screen)
        pygame.display.flip()


def run() -> None:
    pygame.init()
    audio = AudioSystem()
    try:
        while True:
            selected_level = _run_main_menu(audio)
            if selected_level is None:
                break
            should_return_to_menu = TowerDefenseApp(selected_level, audio).run()
            if not should_return_to_menu:
                break
    finally:
        audio.stop()
        pygame.quit()
