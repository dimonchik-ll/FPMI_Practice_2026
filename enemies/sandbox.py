from __future__ import annotations

import pygame

from core.map_model import GameMap
from core.map_renderer import MapRenderer
from enemies.api import EnemySystem, wave_plan_for
from shared.contracts import DamageCommand, GameEvent, GameEventKind


def event_message(event: GameEvent) -> str:
    if event.kind == GameEventKind.ENEMY_DEFEATED:
        return f"Враг побеждён: +{event.payload['reward']} золота"

    if event.kind == GameEventKind.ENEMY_REACHED_GOAL:
        return f"База получила урон: -{event.payload['damage']}"

    if event.kind == GameEventKind.WAVE_COMPLETED:
        return f"Волна {event.payload['wave_number']} завершена"

    return str(event.payload)


def start_selected_wave(
    enemies: EnemySystem,
    wave_number: int,
    route: tuple,
) -> bool:
    if not enemies.start_wave(wave_number, route):
        return False

    enemy_count = len(wave_plan_for(wave_number))
    print(f"Запущена волна {wave_number}: {enemy_count} врагов")
    return True


def main() -> None:
    pygame.init()

    game_map = GameMap.create_default()
    screen = pygame.display.set_mode(
        (game_map.pixel_width, game_map.pixel_height)
    )
    pygame.display.set_caption("Enemies sandbox")

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 26)
    small_font = pygame.font.Font(None, 20)

    renderer = MapRenderer()
    enemies = EnemySystem()
    route = game_map.build_route()

    next_wave = 1
    messages: list[tuple[str, float]] = []
    running = True

    while running:
        delta_time = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_SPACE:
                active_enemies = enemies.views()

                if active_enemies:
                    target = active_enemies[0]
                    events = enemies.apply_damage(
                        [
                            DamageCommand(
                                target_id=target.identifier,
                                amount=35,
                                source_id="sandbox",
                            )
                        ]
                    )

                    for game_event in events:
                        text = event_message(game_event)
                        print(text)
                        messages.append((text, 2.5))

            wave_keys = {
                pygame.K_1: 1,
                pygame.K_2: 2,
                pygame.K_3: 3,
                pygame.K_4: 4,
            }

            chosen_wave = wave_keys.get(event.key)

            if chosen_wave is not None:
                if start_selected_wave(enemies, chosen_wave, route):
                    next_wave = chosen_wave + 1
                    messages.append(
                        (
                            f"Запущена волна {chosen_wave}",
                            2.5,
                        )
                    )

            if event.key == pygame.K_n:
                if start_selected_wave(enemies, next_wave, route):
                    messages.append(
                        (
                            f"Запущена волна {next_wave}",
                            2.5,
                        )
                    )
                    next_wave += 1

        for game_event in enemies.update(delta_time):
            text = event_message(game_event)
            print(text)
            messages.append((text, 2.5))

        screen.fill((25, 35, 25))
        renderer.draw(screen, game_map)
        enemies.draw(screen)

        title = font.render(
            f"Следующая волна: {next_wave}",
            True,
            (245, 245, 245),
        )
        screen.blit(title, (12, 12))

        help_text = small_font.render(
            "1-4: волны | N: следующая волна | "
            "SPACE: урон | ESC: выход",
            True,
            (245, 245, 245),
        )
        screen.blit(help_text, (12, 42))

        updated_messages: list[tuple[str, float]] = []

        for message, remaining_time in messages:
            if remaining_time > 0:
                updated_messages.append(
                    (message, remaining_time - delta_time)
                )

        messages = updated_messages[-5:]

        for index, (message, _) in enumerate(messages):
            text = small_font.render(
                message,
                True,
                (255, 226, 115),
            )
            screen.blit(text, (12, 70 + index * 22))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()