import pygame
from pygame.math import Vector2


class Tower:
    def __init__(self, x, y):
        self.position = Vector2(x, y)

        self.range = 130
        self.damage = 25
        self.attack_delay = 0.7
        self.attack_timer = 0.0

        self.size = 22

    def find_target(self, enemies):
        closest_enemy = None
        closest_distance = self.range

        for enemy in enemies:
            if not enemy.alive:
                continue

            distance = self.position.distance_to(enemy.position)

            if distance <= closest_distance:
                closest_enemy = enemy
                closest_distance = distance

        return closest_enemy

    def update(self, dt, enemies):
        self.attack_timer += dt

        target = self.find_target(enemies)

        if target is not None and self.attack_timer >= self.attack_delay:
            target.take_damage(self.damage)
            self.attack_timer = 0.0

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            (70, 120, 255),
            (int(self.position.x), int(self.position.y)),
            self.size
        )

        pygame.draw.circle(
            screen,
            (130, 170, 255),
            (int(self.position.x), int(self.position.y)),
            self.range,
            1
        )