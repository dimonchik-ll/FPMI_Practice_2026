from __future__ import annotations

from dataclasses import dataclass

import pygame

from shared.contracts import (
    GameSnapshot,
    TOWER_DEFINITIONS,
    TowerKind,
    UiAction,
    UiActionKind,
)

PANEL_WIDTH = 270


@dataclass(frozen=True, slots=True)
class _Button:
    label: str
    rect: pygame.Rect
    action: UiAction


class UiSystem:
    def __init__(self, map_width: int, height: int) -> None:
        self._map_width = map_width
        self._height = height
        self._font = pygame.font.Font(None, 27)
        self._title_font = pygame.font.Font(None, 34)
        self._buttons = self._build_buttons()

    def handle_event(self, event: pygame.event.Event) -> UiAction | None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        for button in self._buttons:
            if button.rect.collidepoint(event.pos):
                return button.action
        return None

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        panel = pygame.Rect(self._map_width, 0, PANEL_WIDTH, self._height)
        pygame.draw.rect(surface, (31, 40, 48), panel)
        pygame.draw.line(surface, (85, 103, 117), (self._map_width, 0), (self._map_width, self._height), 2)

        self._draw_text(surface, "Tower Defense", self._map_width + 20, 18, self._title_font, (243, 239, 212))
        self._draw_text(surface, f"Деньги: {snapshot.player.money}", self._map_width + 20, 66)
        self._draw_text(surface, f"Жизни: {snapshot.player.lives}", self._map_width + 20, 94)
        self._draw_text(surface, f"Волна: {snapshot.wave_number}", self._map_width + 20, 122)
        self._draw_text(surface, f"Счёт: {snapshot.player.score}", self._map_width + 20, 150)
        self._draw_text(surface, "Выбор башни", self._map_width + 20, 196, self._title_font, (189, 214, 176))

        for button in self._buttons:
            is_selected = (
                button.action.kind == UiActionKind.SELECT_TOWER
                and button.action.payload is not None
                and button.action.payload.get("tower_kind") == snapshot.player.selected_tower
            )
            color = (105, 144, 95) if is_selected else (67, 89, 104)
            pygame.draw.rect(surface, color, button.rect, border_radius=7)
            pygame.draw.rect(surface, (196, 213, 220), button.rect, 2, border_radius=7)
            label = self._font.render(button.label, True, (245, 246, 240))
            surface.blit(label, label.get_rect(center=button.rect.center))

        status = "Волна идёт" if snapshot.wave_is_active else "Нажми «Старт волны»"
        self._draw_text(surface, status, self._map_width + 20, self._height - 90, color=(232, 202, 124))

    def _build_buttons(self) -> list[_Button]:
        buttons: list[_Button] = []
        y = 240
        for tower_kind in TowerKind:
            definition = TOWER_DEFINITIONS[tower_kind]
            buttons.append(
                _Button(
                    label=f"{definition.title} — {definition.cost}",
                    rect=pygame.Rect(self._map_width + 18, y, PANEL_WIDTH - 36, 42),
                    action=UiAction(UiActionKind.SELECT_TOWER, {"tower_kind": tower_kind}),
                )
            )
            y += 52
        buttons.append(
            _Button(
                label="Старт волны",
                rect=pygame.Rect(self._map_width + 18, self._height - 56, PANEL_WIDTH - 36, 40),
                action=UiAction(UiActionKind.START_WAVE),
            )
        )
        return buttons

    @staticmethod
    def _draw_text(
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        font: pygame.font.Font | None = None,
        color: tuple[int, int, int] = (236, 238, 235),
    ) -> None:
        actual_font = font or pygame.font.Font(None, 27)
        surface.blit(actual_font.render(text, True, color), (x, y))
