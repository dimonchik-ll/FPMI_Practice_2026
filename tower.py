import pygame
from entity import Entity
from constants import *
import math

class Tower(Entity):
    def __init__(self):
        self.positions = self.find_positions()

    def find_positions(self):
        positions = []

        for row in range(rows):
            for col in range(cols):
                if field[row][col] == 1:
                    positions.append((col, row))

        return positions
    
    def draw(self, surface, color):
        radius = CELL_SIZE // 3

        for col, row in self.positions:
            center_x = col * CELL_SIZE + CELL_SIZE // 2
            center_y = row * CELL_SIZE + CELL_SIZE // 2

            points = []
            for i in range(6):
                angle_deg = 60 * i
                angle_rad = math.radians(angle_deg)
                x = center_x + radius * math.cos(angle_rad)
                y = center_y + radius * math.sin(angle_rad)
                points.append((x, y))

            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

    def update(self): pass