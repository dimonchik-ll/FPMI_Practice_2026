from abc import ABC, abstractmethod
from Entities.entity_base import EntityBase

class TowerBase(EntityBase, ABC):

    def __init__(self, x, y, image):
        self.x = x
        self.y = y

        self.image = image

        self.range = 180
        self.damage = 10
        self.reload_time = 60
        self.reload = 0

        self.target = None

    def update(self, enemies, bullets):
        if self.reload > 0:
            self.reload -= 1

        self.target = self.find_target(enemies)

        if self.target and self.reload == 0:
            bullets.append(self.shoot())
            self.reload = self.reload_time

    def find_target(self, enemies):
        nearest = None
        nearest_distance = float("inf")

        for enemy in enemies:

            if enemy.end_of_path:
                continue

            dx = enemy.x - self.x
            dy = enemy.y - self.y

            distance = (dx * dx + dy * dy) ** 0.5

            if distance <= self.range and distance < nearest_distance:
                nearest = enemy
                nearest_distance = distance

        return nearest

    @abstractmethod
    def shoot(self):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.image.get_rect(center=(self.x, self.y)))