from __future__ import annotations

from abc import ABC, abstractmethod

import pygame

from shared.contracts import GameSnapshot, UiAction
from ui.theme import Color


class UiComponent(ABC):
    def handle_event(
        self,
        event: pygame.event.Event,
        snapshot: GameSnapshot | None,
    ) -> UiAction | None:
        return None

    @abstractmethod
    def draw(self, surface: pygame.Surface, snapshot: GameSnapshot) -> None:
        pass


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Color,
    position: tuple[int, int],
) -> None:
    surface.blit(font.render(text, True, color), position)


def draw_text_right(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Color,
    position: tuple[int, int],
) -> None:
    rendered = font.render(text, True, color)
    surface.blit(rendered, (position[0] - rendered.get_width(), position[1]))


def draw_centered_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Color,
    rect: pygame.Rect,
) -> None:
    rendered = font.render(text, True, color)
    surface.blit(rendered, rendered.get_rect(center=rect.center))


def wrap_text(
    text: str,
    font: pygame.font.Font,
    max_width: int,
) -> tuple[str, ...]:
    if max_width <= 0:
        return ()

    words = text.split()

    if not words:
        return ()

    lines: list[str] = []
    current_line = ""

    for word in words:
        candidate = f"{current_line} {word}".strip()

        if font.size(candidate)[0] <= max_width:
            current_line = candidate
            continue

        if current_line:
            lines.append(current_line)
            current_line = ""

        while font.size(word)[0] > max_width:
            part = ""

            for character in word:
                candidate_part = part + character

                if font.size(candidate_part)[0] > max_width:
                    break

                part = candidate_part

            if not part:
                part = word[0]

            lines.append(part)
            word = word[len(part):]

        current_line = word

    if current_line:
        lines.append(current_line)

    return tuple(lines)


def ellipsize(
    text: str,
    font: pygame.font.Font,
    max_width: int,
) -> str:
    if font.size(text)[0] <= max_width:
        return text

    suffix = "…"
    shortened = text

    while shortened and font.size(shortened + suffix)[0] > max_width:
        shortened = shortened[:-1]

    return shortened + suffix if shortened else suffix