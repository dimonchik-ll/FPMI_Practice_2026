from __future__ import annotations

import pygame

from shared.contracts import GameSnapshot, PlayerState, UiActionKind
from ui.api import PANEL_WIDTH, UiSystem


def main() -> None:
    pygame.init()

    map_width, height = 640, 480
    screen = pygame.display.set_mode((map_width + PANEL_WIDTH, height))
    pygame.display.set_caption("UI sandbox — M: +20 денег, N: завершить волну")

    ui = UiSystem(map_width, height)
    player = PlayerState()

    wave_number = 1
    wave_is_active = False
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    player.money += 20
                elif event.key == pygame.K_n and wave_is_active:
                    wave_is_active = False
                    wave_number += 1

            action = ui.handle_event(event)

            if action is None:
                continue

            if action.kind == UiActionKind.SELECT_TOWER and action.payload is not None:
                player.selected_tower = action.payload["tower_kind"]
            elif action.kind == UiActionKind.START_WAVE:
                wave_is_active = True

        snapshot = GameSnapshot(
            player=player.to_view(),
            wave_number=wave_number,
            enemies=(),
            towers=(),
            wave_is_active=wave_is_active,
            game_over=False,
            victory=False,
        )

        screen.fill((77, 128, 77))
        pygame.draw.rect(screen, (93, 145, 90), (0, 0, map_width, height))

        ui.draw(screen, snapshot)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()