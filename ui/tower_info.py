from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot, TOWER_DEFINITIONS, TowerKind
from ui.layout import UiLayout
from ui.theme import Color, UiFonts, UiTheme
from ui.widgets import draw_text, ellipsize, wrap_text

_TOWER_HINTS: dict[TowerKind, str] = {
    TowerKind.ARCHER_1: "Дешёвая и быстрая башня для первых волн.",
    TowerKind.ARCHER_2: "Пробивающая стрела задевает двух врагов подряд.",
    TowerKind.ARCHER_3: "Первый уровень атаки по области.",
    TowerKind.ARCHER_4: "Увеличенный радиус взрыва для плотных волн.",
    TowerKind.ARCHER_5: "Сильная башня по области для середины игры.",
    TowerKind.ARCHER_6: "Большой урон и широкий радиус взрыва.",
    TowerKind.ARCHER_7: "Элитный лучник для самых сложных волн.",
    TowerKind.ARCHER_8: "Максимальный уровень: огромный урон и дальность.",
}


class TowerInfoPanel:
    _PADDING_X = 10
    _PADDING_Y = 8
    _TEXT_GAP = 4
    _HEADER_GAP = 5

    def __init__(
        self,
        layout: UiLayout,
        theme: UiTheme,
        fonts: UiFonts,
    ) -> None:
        self._layout = layout
        self._theme = theme
        self._fonts = fonts

    def draw(
        self,
        surface: pygame.Surface,
        snapshot: GameSnapshot,
        hovered_tower: TowerKind | None,
    ) -> None:
        area = self._layout.tower_info_area()

        if area.height <= 0:
            return

        draw_text(
            surface,
            "ИНФОРМАЦИЯ",
            self._fonts.section,
            (190, 216, 179),
            (area.x, area.y),
        )

        card_top = area.y + self._fonts.section.get_linesize() + self._HEADER_GAP
        max_card_height = area.bottom - card_top

        if max_card_height <= 0:
            return

        tower_kind = hovered_tower or snapshot.player.selected_tower
        title, description, footer, footer_color = self._content(
            tower_kind,
            snapshot,
        )

        text_width = area.width - self._PADDING_X * 2
        description_lines = wrap_text(
            description,
            self._fonts.small,
            text_width,
        )

        visible_lines, visible_footer = self._fit_content(
            description_lines,
            footer,
            max_card_height,
            text_width,
        )

        minimum_height = self._minimum_card_height()

        if max_card_height < minimum_height:
            return

        card_height = self._card_height(visible_lines, visible_footer)
        card_rect = pygame.Rect(
            area.x,
            card_top,
            area.width,
            card_height,
        )

        pygame.draw.rect(
            surface,
            self._theme.hint_background,
            card_rect,
            border_radius=9,
        )
        pygame.draw.rect(
            surface,
            self._theme.hint_border,
            card_rect,
            width=1,
            border_radius=9,
        )

        y = card_rect.y + self._PADDING_Y

        draw_text(
            surface,
            title,
            self._fonts.body,
            self._theme.title_text,
            (card_rect.x + self._PADDING_X, y),
        )

        y += self._fonts.body.get_linesize() + self._TEXT_GAP

        for line in visible_lines:
            draw_text(
                surface,
                line,
                self._fonts.small,
                self._theme.body_text,
                (card_rect.x + self._PADDING_X, y),
            )
            y += self._fonts.small.get_linesize()

        if visible_footer is not None:
            y += self._TEXT_GAP

            draw_text(
                surface,
                visible_footer,
                self._fonts.small,
                footer_color,
                (card_rect.x + self._PADDING_X, y),
            )

    def _content(
        self,
        tower_kind: TowerKind | None,
        snapshot: GameSnapshot,
    ) -> tuple[str, str, str | None, Color]:
        if tower_kind is None:
            return (
                "Выберите башню",
                "Нажмите на карточку ниже, чтобы увидеть характеристики.",
                None,
                self._theme.body_text,
            )

        definition = TOWER_DEFINITIONS[tower_kind]
        missing_money = definition.cost - snapshot.player.money

        if missing_money > 0:
            footer = f"Не хватает {missing_money} монет."
            footer_color: Color = (238, 150, 132)
        else:
            footer = "ЛКМ по месту строительства."
            footer_color = (171, 222, 171)

        return (
            definition.title,
            _TOWER_HINTS.get(tower_kind, "Башня с улучшенными характеристиками."),
            footer,
            footer_color,
        )

    def _fit_content(
        self,
        lines: tuple[str, ...],
        footer: str | None,
        max_height: int,
        text_width: int,
    ) -> tuple[tuple[str, ...], str | None]:
        full_height = self._card_height(lines, footer)

        if full_height <= max_height:
            return lines, footer

        no_footer_height = self._card_height(lines, None)

        if no_footer_height <= max_height:
            return lines, None

        fixed_height = (
            self._PADDING_Y * 2
            + self._fonts.body.get_linesize()
            + self._TEXT_GAP
        )

        max_lines = max(
            0,
            (max_height - fixed_height) // self._fonts.small.get_linesize(),
        )

        if max_lines == 0:
            return (), None

        visible_lines = list(lines[:max_lines])

        if len(lines) > max_lines:
            visible_lines[-1] = ellipsize(
                visible_lines[-1] + "…",
                self._fonts.small,
                text_width,
            )

        return tuple(visible_lines), None

    def _minimum_card_height(self) -> int:
        return self._PADDING_Y * 2 + self._fonts.body.get_linesize()

    def _card_height(
        self,
        lines: tuple[str, ...],
        footer: str | None,
    ) -> int:
        height = (
            self._PADDING_Y * 2
            + self._fonts.body.get_linesize()
        )

        if lines:
            height += self._TEXT_GAP
            height += len(lines) * self._fonts.small.get_linesize()

        if footer is not None:
            height += self._TEXT_GAP
            height += self._fonts.small.get_linesize()

        return height