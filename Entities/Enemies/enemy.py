import pygame
from pygame.math import Vector2


class Enemy:
    def __init__(self, path, speed=90, health=100):
        self.path = [Vector2(point) for point in path]
        self.position = self.path[0].copy()

        self.speed = speed
        self.health = health
        self.max_health = health

        self.target_index = 1
        self.radius = 10
        self.alive = True

    def update(self, dt):
        if not self.alive:
            return

        if self.target_index >= len(self.path):
            self.alive = False
            return

        target = self.path[self.target_index]
        direction = target - self.position
        distance = direction.length()

        if distance == 0:
            self.target_index += 1
            return

        move_distance = self.speed * dt

        if move_distance >= distance:
            self.position = target.copy()
            self.target_index += 1
        else:
            self.position += direction.normalize() * move_distance

    def take_damage(self, damage):
        self.health -= damage

        if self.health <= 0:
            self.alive = False

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            (220, 60, 60),
            (int(self.position.x), int(self.position.y)),
            self.radius
        )

        bar_width = 24
        bar_height = 4

        health_width = int(bar_width * self.health / self.max_health)

        pygame.draw.rect(
            screen,
            (70, 70, 70),
            (
                int(self.position.x - bar_width // 2),
                int(self.position.y - 20),
                bar_width,
                bar_height
            )
        )

        pygame.draw.rect(
            screen,
            (40, 220, 70),
            (
                int(self.position.x - bar_width // 2),
                int(self.position.y - 20),
                health_width,
                bar_height
            )
        )