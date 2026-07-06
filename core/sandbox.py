from __future__ import annotations

import argparse

import pygame

from core.map_model import GameMap
from core.map_renderer import MapRenderer


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Запуск песочницы карты.",
    )

    parser.add_argument(
        "level",
        nargs="?",
        type=int,
        default=1,
        help="Номер уровня для запуска. По умолчанию: 1.",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    pygame.init()

    try:
        game_map = GameMap.create_from_level(arguments.level)
    except ValueError as error:
        pygame.quit()
        raise SystemExit(str(error)) from error

    screen = pygame.display.set_mode(
        (
            game_map.pixel_width,
            game_map.pixel_height,
        )
    )

    pygame.display.set_caption(
        f"Core sandbox — Level {arguments.level}"
    )

    print(
        f"Уровень {arguments.level}: "
        f"{game_map.cols}x{game_map.rows}, "
        f"тайл {game_map.tile_size}px, "
        f"точек маршрута: {len(game_map.build_route())}"
    )

    clock = pygame.time.Clock()
    renderer = MapRenderer()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                row = event.pos[1] // game_map.tile_size
                col = event.pos[0] // game_map.tile_size
                game_map.occupy((row, col))

        screen.fill((25, 35, 25))
        renderer.draw(screen, game_map)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()