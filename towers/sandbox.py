import pygame

from shared.contracts import BuildRequest, EnemyKind, EnemyView, TowerKind, Vector2
from towers.api import TowerSystem


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((640, 420))
    pygame.display.set_caption("Towers sandbox")
    clock = pygame.time.Clock()
    towers = TowerSystem()
    towers.build(BuildRequest(TowerKind.ARCHER_1, (3, 3), Vector2(180, 230)))
    enemy = EnemyView("demo-enemy", EnemyKind.ENEMY_1, Vector2(430, 230), 200, 200, 0, 0, 0)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        towers.update(clock.get_time() / 1000.0, (enemy,))
        screen.fill((65, 104, 61))
        towers.draw(screen)
        pygame.draw.circle(screen, (190, 64, 80), (int(enemy.position.x), int(enemy.position.y)), 17)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
