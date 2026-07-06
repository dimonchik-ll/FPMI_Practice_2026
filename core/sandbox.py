from __future__ import annotations

import pygame

from core.map_model import BuildZone, GameMap
from core.map_renderer import MapRenderer


def get_zone_rect(
    game_map: GameMap,
    zone: BuildZone,
) -> pygame.Rect:
    rows = [row for row, _ in zone.cells]
    cols = [col for _, col in zone.cells]

    min_row = min(rows)
    max_row = max(rows)
    min_col = min(cols)
    max_col = max(cols)

    return pygame.Rect(
        min_col * game_map.tile_size,
        min_row * game_map.tile_size,
        (max_col - min_col + 1) * game_map.tile_size,
        (max_row - min_row + 1) * game_map.tile_size,
    )


def draw_build_zone_state(
    screen: pygame.Surface,
    game_map: GameMap,
) -> None:
    for zone in game_map.build_zones.values():
        rect = get_zone_rect(game_map, zone)

        is_occupied = not zone.cells.isdisjoint(
            game_map.occupied_cells
        )

        if is_occupied:
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((220, 70, 60, 120))
            screen.blit(overlay, rect.topleft)

            pygame.draw.rect(
                screen,
                (255, 90, 80),
                rect,
                width=3,
            )

            center = (
                int(zone.center.x),
                int(zone.center.y),
            )

            pygame.draw.circle(screen, (70, 45, 45), center, 16)
            pygame.draw.circle(screen, (255, 220, 120), center, 10)
        else:
            pygame.draw.rect(
                screen,
                (80, 220, 120),
                rect,
                width=1,
            )


def main() -> None:
    pygame.init()

    game_map = GameMap.create_default()

    screen = pygame.display.set_mode(
        (
            game_map.pixel_width,
            game_map.pixel_height,
        )
    )

    pygame.display.set_caption("Core sandbox")
    clock = pygame.time.Clock()
    renderer = MapRenderer()

    print("ЛКМ — занять зону строительства.")
    print("ПКМ — освободить зону строительства.")

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                row = event.pos[1] // game_map.tile_size
                col = event.pos[0] // game_map.tile_size
                cell = (row, col)

                zone = game_map.get_build_zone(cell)

                if event.button == 1:
                    if zone is None:
                        print("Курсор не находится в зоне строительства.")
                        continue

                    if game_map.occupy(cell):
                        print(
                            f"Зона {zone.zone_id} занята. "
                            f"Центр башни: {zone.center}"
                        )
                    else:
                        print(
                            f"Зона {zone.zone_id} уже занята."
                        )

                elif event.button == 3:
                    if zone is None:
                        print("Курсор не находится в зоне строительства.")
                        continue

                    game_map.release(cell)
                    print(f"Зона {zone.zone_id} освобождена.")

        screen.fill((25, 35, 25))
        renderer.draw(screen, game_map)
        draw_build_zone_state(screen, game_map)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()