import pygame

from core.map_model import GameMap
from core.map_renderer import MapRenderer
from enemies.api import EnemySystem


def main() -> None:
    pygame.init()
    game_map = GameMap.create_default()
    screen = pygame.display.set_mode((game_map.pixel_width, game_map.pixel_height))
    pygame.display.set_caption("Enemies sandbox")
    clock = pygame.time.Clock()
    renderer = MapRenderer()
    enemies = EnemySystem()
    enemies.start_wave(1, game_map.build_route())
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        enemies.update(clock.get_time() / 1000.0)
        screen.fill((25, 35, 25))
        renderer.draw(screen, game_map)
        enemies.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
