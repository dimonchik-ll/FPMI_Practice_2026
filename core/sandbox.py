import pygame

from core.map_model import GameMap
from core.map_renderer import MapRenderer


def main() -> None:
    pygame.init()
    game_map = GameMap.create_default()
    screen = pygame.display.set_mode((game_map.pixel_width, game_map.pixel_height))
    pygame.display.set_caption("Core sandbox")
    clock = pygame.time.Clock()
    renderer = MapRenderer()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
