from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import pygame

Color: TypeAlias = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class UiTheme:
    panel_background: Color = (24, 33, 42)
    panel_border: Color = (100, 128, 146)
    title_text: Color = (246, 238, 194)
    body_text: Color = (239, 244, 239)
    muted_text: Color = (185, 201, 208)

    stat_background: Color = (38, 52, 64)
    default_card: Color = (48, 69, 82)
    default_card_border: Color = (104, 132, 146)
    hover_card: Color = (59, 88, 105)
    hover_card_border: Color = (169, 213, 230)
    selected_card: Color = (64, 106, 78)
    selected_card_border: Color = (238, 226, 151)
    unavailable_card: Color = (49, 55, 61)
    unavailable_card_border: Color = (85, 93, 100)

    hint_background: Color = (34, 47, 59)
    hint_border: Color = (91, 119, 136)


class UiFonts:
    def __init__(self) -> None:
        self.title = self._make_font(32, bold=True)
        self.section = self._make_font(24, bold=True)
        self.body = self._make_font(22)
        self.small = self._make_font(18)

    @staticmethod
    def _make_font(size: int, bold: bool = False) -> pygame.font.Font:
        for font_name in ("tahoma", "verdana", "segoeui", "arial"):
            font_path = pygame.font.match_font(font_name, bold=bold)

            if font_path is not None:
                return pygame.font.Font(font_path, size)

        return pygame.font.Font(None, size)