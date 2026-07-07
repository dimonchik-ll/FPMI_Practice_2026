from __future__ import annotations

import pygame

from enemies.api import EnemySystem, wave_plan_for
from shared.contracts import DamageCommand, GameEvent, GameEventKind, Vector2


SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640

SANDBOX_ROUTE: tuple[Vector2, ...] = (
    Vector2(55, 555),
    Vector2(230, 555),
    Vector2(230, 165),
    Vector2(500, 165),
    Vector2(500, 420),
    Vector2(765, 420),
    Vector2(765, 85),
    Vector2(905, 85),
)


def event_message(event: GameEvent) -> str:
    if event.kind == GameEventKind.ENEMY_DEFEATED:
        return f"Враг побеждён: +{event.payload['reward']} золота"

    if event.kind == GameEventKind.ENEMY_REACHED_GOAL:
        return f"База получила урон: -{event.payload['damage']}"

    if event.kind == GameEventKind.WAVE_COMPLETED:
        return f"Волна {event.payload['wave_number']} завершена"

    return str(event.payload)


def start_wave(
    enemies: EnemySystem,
    wave_number: int,
) -> str | None:
    if not enemies.start_wave(wave_number, SANDBOX_ROUTE):
        return None

    count = len(wave_plan_for(wave_number))
    message = f"Запущена волна {wave_number}: {count} врагов"
    print(message)
    return message


def draw_route(surface: pygame.Surface) -> None:
    points = [
        (int(point.x), int(point.y))
        for point in SANDBOX_ROUTE
    ]

    pygame.draw.lines(surface, (119, 90, 55), False, points, 46)
    pygame.draw.lines(surface, (179, 145, 91), False, points, 36)

    pygame.draw.circle(surface, (70, 185, 85), points[0], 18)
    pygame.draw.circle(surface, (193, 71, 66), points[-1], 18)


def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Enemies Stage 2 sandbox")

    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 28)
    text_font = pygame.font.Font(None, 21)

    enemies = EnemySystem()
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
                continue

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
                        message = event_message(damage_event)
                        print(message)
                        messages.append((message, 2.5))

            wave_keys = {
                pygame.K_1: 1,
                pygame.K_2: 2,
                pygame.K_3: 3,
                pygame.K_4: 4,
            }

            selected_wave = wave_keys.get(event.key)

            if selected_wave is not None:
                message = start_wave(enemies, selected_wave)

                if message is not None:
                    next_wave = selected_wave + 1
                    messages.append((message, 2.5))

            if event.key == pygame.K_n:
                message = start_wave(enemies, next_wave)

                if message is not None:
                    messages.append((message, 2.5))
                    next_wave += 1

        for game_event in enemies.update(delta_time):
            message = event_message(game_event)
            print(message)
            messages.append((message, 2.5))

        screen.fill((45, 105, 70))
        draw_route(screen)
        enemies.draw(screen)

        title = title_font.render(
            f"Следующая волна: {next_wave}",
            True,
            (245, 245, 245),
        )
        screen.blit(title, (14, 12))

        hint = text_font.render(
            "1-4: волны | N: следующая | Space: урон | Esc: выход",
            True,
            (245, 245, 245),
        )
        screen.blit(hint, (14, 42))

        active_text = text_font.render(
            f"Активно врагов: {len(enemies.views())}",
            True,
            (255, 226, 115),
        )
        screen.blit(active_text, (14, 67))

        updated_messages: list[tuple[str, float]] = []

        for message, remaining in messages:
            if remaining > 0:
                updated_messages.append(
                    (message, remaining - delta_time)
                )

        messages = updated_messages[-5:]

        for index, (message, _) in enumerate(messages):
            rendered = text_font.render(
                message,
                True,
                (255, 226, 115),
            )
            screen.blit(rendered, (14, 96 + index * 22))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()