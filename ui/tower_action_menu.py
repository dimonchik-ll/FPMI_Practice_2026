from __future__ import annotations

import pygame

from shared.contracts import (
    GameSnapshot,
    TOWER_DEFINITIONS,
    TowerView,
    UiAction,
    UiActionKind,
    next_tower_kind,
    tower_max_level,
)
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import draw_centered_text, draw_text


_ATTACK_TYPE_LABELS = {
    "single": "Одиночная",
    "piercing": "Пробивающая",
    "splash": "По области",
}


class TowerActionMenu:
    """Modal menu displayed after a right-click on an installed tower."""

    _WIDTH = 332
    _HEIGHT = 354
    _PADDING = 16
    _ROW_GAP = 5
    _BUTTON_HEIGHT = 40

    def __init__(self, layout: UiLayout, theme: UiTheme, fonts: UiFonts) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts
        self._tower_id: str | None = None

    @property
    def is_open(self) -> bool:
        return self._tower_id is not None

    def open(self, tower_identifier: str) -> None:
        self._tower_id = tower_identifier

    def close(self) -> None:
        self._tower_id = None

    def sync(self, snapshot: GameSnapshot) -> None:
        if self._tower_id is None:
            return
        if self._selected_tower(snapshot) is None:
            self.close()

    def contains_point(self, position: tuple[int, int]) -> bool:
        return self.is_open and self._menu_rect().collidepoint(position)

    def handle_event(
        self,
        event: pygame.event.Event,
        snapshot: GameSnapshot,
    ) -> UiAction | None:
        self.sync(snapshot)
        tower = self._selected_tower(snapshot)
        if tower is None:
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return UiAction(UiActionKind.CLOSE_TOWER_MENU)

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        menu = self._menu_rect()
        if not menu.collidepoint(event.pos):
            return UiAction(UiActionKind.CLOSE_TOWER_MENU)

        if self._close_button_rect().collidepoint(event.pos):
            return UiAction(UiActionKind.CLOSE_TOWER_MENU)

        if self._upgrade_button_rect().collidepoint(event.pos):
            if self._can_upgrade(tower, snapshot):
                return UiAction(
                    UiActionKind.UPGRADE_TOWER,
                    {"tower_id": tower.identifier},
                )
            return None

        if self._delete_button_rect().collidepoint(event.pos):
            return UiAction(
                UiActionKind.REMOVE_TOWER,
                {"tower_id": tower.identifier},
            )

        return None

    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        self.sync(snapshot)
        tower = self._selected_tower(snapshot)
        if tower is None:
            return

        map_area = pygame.Rect(0, 0, self._layout.map_width, self._layout.height)
        shade = pygame.Surface(map_area.size, pygame.SRCALPHA)
        shade.fill((8, 13, 19, 118))
        surface.blit(shade, map_area.topleft)

        menu = self._menu_rect()
        pygame.draw.rect(surface, self._theme.panel_background, menu, border_radius=12)
        pygame.draw.rect(surface, self._theme.panel_border, menu, width=2, border_radius=12)

        title = TOWER_DEFINITIONS[tower.kind].title.upper()
        draw_text(
            surface,
            title,
            self._fonts.section,
            self._theme.title_text,
            (menu.x + self._PADDING, menu.y + 12),
        )

        close_rect = self._close_button_rect()
        pygame.draw.rect(surface, self._theme.default_card, close_rect, border_radius=6)
        pygame.draw.rect(surface, self._theme.panel_border, close_rect, width=1, border_radius=6)
        draw_centered_text(surface, "×", self._fonts.body, self._theme.body_text, close_rect)

        y = menu.y + 56
        draw_text(
            surface,
            "ХАРАКТЕРИСТИКИ",
            self._fonts.small,
            self._theme.muted_text,
            (menu.x + self._PADDING, y),
        )
        y += self._fonts.small.get_linesize() + self._ROW_GAP + 2

        for label, value in self._stat_rows(tower):
            draw_text(
                surface,
                label,
                self._fonts.small,
                self._theme.muted_text,
                (menu.x + self._PADDING, y),
            )
            value_width = self._fonts.small.size(value)[0]
            draw_text(
                surface,
                value,
                self._fonts.small,
                self._theme.body_text,
                (menu.right - self._PADDING - value_width, y),
            )
            y += self._fonts.small.get_linesize() + self._ROW_GAP

        self._draw_upgrade_button(surface, tower, snapshot)
        self._draw_delete_button(surface)

    def _selected_tower(self, snapshot: GameSnapshot) -> TowerView | None:
        if self._tower_id is None:
            return None
        return next(
            (tower for tower in snapshot.towers if tower.identifier == self._tower_id),
            None,
        )

    def _menu_rect(self) -> pygame.Rect:
        width = min(self._WIDTH, max(240, self._layout.map_width - 28))
        height = self._HEIGHT
        x = max(14, (self._layout.map_width - width) // 2)
        y = max(28, (self._layout.height - height) // 2)
        return pygame.Rect(x, y, width, height)

    def _close_button_rect(self) -> pygame.Rect:
        menu = self._menu_rect()
        size = 30
        return pygame.Rect(menu.right - self._PADDING - size, menu.y + 12, size, size)

    def _upgrade_button_rect(self) -> pygame.Rect:
        menu = self._menu_rect()
        return pygame.Rect(
            menu.x + self._PADDING,
            menu.bottom - self._PADDING * 2 - self._BUTTON_HEIGHT * 2,
            menu.width - self._PADDING * 2,
            self._BUTTON_HEIGHT,
        )

    def _delete_button_rect(self) -> pygame.Rect:
        upgrade = self._upgrade_button_rect()
        return pygame.Rect(
            upgrade.x,
            upgrade.bottom + self._PADDING,
            upgrade.width,
            self._BUTTON_HEIGHT,
        )

    @staticmethod
    def _stat_rows(tower: TowerView) -> tuple[tuple[str, str], ...]:
        return (
            ("Уровень", f"{tower.level} / {tower_max_level()}"),
            ("Урон", str(tower.damage)),
            ("Дальность", str(round(tower.attack_range))),
            ("Скорость", f"{tower.attacks_per_second:.1f}/с"),
            ("Атака", _ATTACK_TYPE_LABELS.get(tower.attack_type, tower.attack_type)),
        )

    def _can_upgrade(self, tower: TowerView, snapshot: GameSnapshot) -> bool:
        return tower.can_upgrade and snapshot.player.money >= (tower.upgrade_cost or 0)

    def _upgrade_label(self, tower: TowerView, snapshot: GameSnapshot) -> str:
        if not tower.can_upgrade:
            return "МАКСИМАЛЬНЫЙ УРОВЕНЬ"

        cost = tower.upgrade_cost or 0
        next_kind = next_tower_kind(tower.kind)
        next_title = (
            TOWER_DEFINITIONS[next_kind].title
            if next_kind is not None
            else "следующий уровень"
        )
        if snapshot.player.money < cost:
            return f"НЕ ХВАТАЕТ {cost - snapshot.player.money} МОНЕТ"
        return f"УЛУЧШИТЬ: {next_title} — {cost} МОН."

    def _draw_upgrade_button(
        self,
        surface: pygame.Surface,
        tower: TowerView,
        snapshot: GameSnapshot,
    ) -> None:
        rect = self._upgrade_button_rect()
        can_upgrade = self._can_upgrade(tower, snapshot)

        if can_upgrade:
            fill: Color = self._theme.selected_card
            border: Color = self._theme.selected_card_border
            text_color: Color = self._theme.body_text
        elif tower.can_upgrade:
            fill = self._theme.unavailable_card
            border = self._theme.unavailable_card_border
            text_color = self._theme.muted_text
        else:
            fill = self._theme.default_card
            border = self._theme.panel_border
            text_color = self._theme.muted_text

        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
        draw_centered_text(
            surface,
            self._upgrade_label(tower, snapshot),
            self._fonts.small,
            text_color,
            rect,
        )

    def _draw_delete_button(self, surface: pygame.Surface) -> None:
        rect = self._delete_button_rect()
        fill: Color = (116, 58, 57)
        border: Color = (223, 137, 128)

        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
        draw_centered_text(
            surface,
            "УДАЛИТЬ БАШНЮ",
            self._fonts.small,
            self._theme.body_text,
            rect,
        )
