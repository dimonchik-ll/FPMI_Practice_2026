import pygame

from shared.contracts import GameSnapshot, PlayerState
from ui.api import PANEL_WIDTH, UiSystem


def main() -> None:
    pygame.init()
    map_width, height = 640, 480
    screen = pygame.display.set_mode((map_width + PANEL_WIDTH, height))
    pygame.display.set_caption("UI sandbox")
    ui = UiSystem(map_width, height)
    player = PlayerState()
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            action = ui.handle_event(event)
            if action and action.payload and "tower_kind" in action.payload:
                player.selected_tower = action.payload["tower_kind"]

        snapshot = GameSnapshot(player.to_view(), 1, (), (), False, False, False)
        screen.fill((76, 123, 69))
        ui.draw(screen, snapshot)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
