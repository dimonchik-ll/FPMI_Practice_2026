from __future__ import annotations

import os

import pygame

from shared.contracts import BuildRequest, EnemyKind, EnemyView, TowerKind, Vector2
from towers.api import TowerSystem


WIDTH = 820
HEIGHT = 520


def make_enemy(identifier: str, position: Vector2, health: int, reward: int) -> EnemyView:
    return EnemyView(
        identifier=identifier,
        kind=EnemyKind.ENEMY_1,
        position=position,
        health=health,
        max_health=health,
        speed=45.0,
        reward=reward,
        base_damage=1,
    )


def draw_enemy(surface, enemy: EnemyView) -> None:
    x = int(enemy.position.x)
    y = int(enemy.position.y)
    ratio = enemy.health_ratio
    pygame.draw.circle(surface, (143, 63, 77), (x, y), 17)
    pygame.draw.rect(surface, (38, 40, 47), (x - 20, y - 30, 40, 7))
    pygame.draw.rect(surface, (95, 203, 115), (x - 20, y - 30, int(40 * ratio), 7))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Towers sandbox — eight upgrade levels")
    font = pygame.font.Font(None, 28)
    clock = pygame.time.Clock()
    max_frames = max(0, int(os.getenv("TOWERS_SANDBOX_MAX_FRAMES", "0")))
    frame_count = 0

    towers = TowerSystem()
    rapid = towers.build(BuildRequest(TowerKind.ARCHER_1, (2, 5), Vector2(150, 340)))
    piercing = towers.build(BuildRequest(TowerKind.ARCHER_1, (6, 5), Vector2(380, 340)))
    ultimate = towers.build(BuildRequest(TowerKind.ARCHER_1, (10, 5), Vector2(610, 340)))
    towers.upgrade(piercing.identifier)
    for _ in range(7):
        towers.upgrade(ultimate.identifier)

    enemies = [
        make_enemy("near-rapid", Vector2(245, 295), 170, 10),
        make_enemy("pierce-front", Vector2(465, 295), 200, 20),
        make_enemy("pierce-back", Vector2(510, 300), 200, 25),
        make_enemy("splash-center", Vector2(685, 295), 230, 35),
        make_enemy("splash-nearby", Vector2(716, 315), 230, 30),
    ]

    total_damage = 0
    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                removed = towers.remove_at_position(Vector2(*event.pos))
                if removed is not None:
                    print(f"Removed {removed.identifier} from cell {removed.cell}")

        commands = towers.update(delta_time, tuple(enemies))
        for command in commands:
            for enemy in enemies:
                if enemy.identifier == command.target_id:
                    enemy.health = max(0, enemy.health - command.amount)
                    total_damage += command.amount

        for enemy in enemies:
            if enemy.health <= 0:
                enemy.health = enemy.max_health

        screen.fill((54, 96, 62))
        pygame.draw.rect(screen, (173, 136, 88), (0, 390, WIDTH, 28))
        towers.draw(screen)
        for enemy in enemies:
            draw_enemy(screen, enemy)

        text = font.render(
            f"Damage commands: {len(commands)} | Total damage: {total_damage} | "
            f"Projectiles: {towers.projectile_count()}",
            True,
            (247, 240, 210),
        )
        screen.blit(text, (20, 20))
        hint = font.render(
            "Eight levels: I — single, II — chain, III–VIII — expanding splash | Right click: remove tower",
            True,
            (247, 240, 210),
        )
        screen.blit(hint, (20, 52))
        pygame.display.flip()

        frame_count += 1
        if max_frames and frame_count >= max_frames:
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()
