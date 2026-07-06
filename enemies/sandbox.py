from __future__ import annotations

import pygame

from core.map_model import GameMap
from core.map_renderer import MapRenderer
from enemies.api import EnemySystem
from shared.contracts import DamageCommand, GameEvent, GameEventKind


def event_message(event: GameEvent) -> str:
    if event.kind == GameEventKind.ENEMY_DEFEATED:
        return f"Enemy defeated: +{event.payload['reward']} gold"

    if event.kind == GameEventKind.ENEMY_REACHED_GOAL:
        return f"Base damaged: -{event.payload['damage']} lives"

    if event.kind == GameEventKind.WAVE_COMPLETED:
        return f"Wave {event.payload['wave_number']} completed"

    return str(event.payload)


def main() -> None:
    pygame.init()

    game_map = GameMap.create_default()
    screen = pygame.display.set_mode(
        (game_map.pixel_width, game_map.pixel_height)
    )
    pygame.display.set_caption("Enemies sandbox")

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)

    renderer = MapRenderer()
    enemies = EnemySystem()
    route = game_map.build_route()

    enemies.start_wave(1, route)

    messages: list[tuple[str, float]] = []
    running = True

    while running:
        delta_time = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_SPACE:
                active_enemies = enemies.views()

                if active_enemies:
                    target = active_enemies[0]

                    damage_events = enemies.apply_damage(
                        [
                            DamageCommand(
                                target_id=target.identifier,
                                amount=35,
                                source_id="sandbox",
                            )
                        ]
                    )

                    for damage_event in damage_events:
                        text = event_message(damage_event)
                        print(text)
                        messages.append((text, 2.5))

            wave_keys = {
                pygame.K_1: 1,
                pygame.K_2: 2,
                pygame.K_3: 3,
                pygame.K_4: 4,
            }

            wave_number = wave_keys.get(event.key)

            if wave_number is not None:
                enemies.start_wave(wave_number, route)

        for game_event in enemies.update(delta_time):
            text = event_message(game_event)
            print(text)
            messages.append((text, 2.5))

        screen.fill((25, 35, 25))
        renderer.draw(screen, game_map)
        enemies.draw(screen)

        help_text = font.render(
            "1-4: start wave | SPACE: damage first enemy | ESC: exit",
            True,
            (245, 245, 245),
        )
        screen.blit(help_text, (12, 12))

        updated_messages: list[tuple[str, float]] = []

        for index, (message, remaining_time) in enumerate(messages):
            if remaining_time <= 0:
                continue

            text = font.render(message, True, (255, 226, 115))
            screen.blit(text, (12, 44 + index * 26))
            updated_messages.append((message, remaining_time - delta_time))

        messages = updated_messages

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()