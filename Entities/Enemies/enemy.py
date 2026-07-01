import pygame
from Entities.entity_base import EntityBase
from constants import *

class Enemy(EntityBase):
    def __init__(self):
        self.path = self.find_path()
        self.current_path_index = 0
        self.x, self.y = self.get_position()
        self.speed = 0.05
        self.progress = 0
        self.end_of_path = False

    def find_path(self):
        zeroes = set()

        for row in range(rows):
            for col in range(cols):
                if field[row][col] == 0 or field[row][col] == 5:
                    zeroes.add((col, row))

        neighbors = {}
        start = None
        end = None

        for x, y in zeroes:
            cur = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy

                if 0 <= nx < cols and 0 <= ny < rows:

                    if field[ny][nx] == 0:
                        cur.append((nx, ny))

                    elif field[ny][nx] == 5:
                        start = (nx, ny)

                    elif field[ny][nx] == 4:
                        end = (nx, ny)

            neighbors[(x, y)] = cur

        path = []
        prev = None
        current = start

        while current is not None:
            path.append(current)

            nxt = None
            for p in neighbors[current]:
                if p != prev:
                    nxt = p
                    break

            prev = current
            current = nxt

        path.append(end)

        return path
    
    def get_position(self):
        x, y = self.path[self.current_path_index]
        return x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2
    
    def update(self):
        self.progress += self.speed

        while self.progress >= 1:
            self.progress -= 1
            self.current_path_index += 1

        if self.current_path_index >= len(self.path) - 1:
            self.end_of_path = True
            return

        current = self.path[self.current_path_index]
        next_point = self.path[self.current_path_index + 1]

        current_x = current[0] * CELL_SIZE + CELL_SIZE // 2
        current_y = current[1] * CELL_SIZE + CELL_SIZE // 2
        next_x = next_point[0] * CELL_SIZE + CELL_SIZE // 2
        next_y = next_point[1] * CELL_SIZE + CELL_SIZE // 2

        self.x = current_x + (next_x - current_x) * self.progress
        self.y = current_y + (next_y - current_y) * self.progress
    
    def draw(self, surface):
        if self.end_of_path:
            return

        pygame.draw.circle(surface, ENEMY_COLOR, (self.x, self.y), CELL_SIZE // 3)
        pygame.draw.circle(surface, BLACK, (self.x, self.y), CELL_SIZE // 3, 1)