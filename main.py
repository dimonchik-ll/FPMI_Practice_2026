import pygame
import sys
import math

pygame.init()

field = [
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    [3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
    [3, 2, 2, 5, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
    [3, 2, 2, 2, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
    [3, 2, 2, 2, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
    [3, 2, 2, 2, 1, 0, 2, 2, 2, 1, 2, 2, 0, 0, 0, 4, 2, 3],
    [3, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 3],
    [3, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
    [3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
]

# Настройки отображения
CELL_SIZE = 60
rows = len(field)
cols = len(field[0])
WINDOW_WIDTH = cols * CELL_SIZE
WINDOW_HEIGHT = rows * CELL_SIZE

GRAY = (99, 99, 99)
LIGHT_GRAY = (168, 168, 168)
GREEN = (104, 181, 96)
RED = (171, 26, 26)
BROWN = (207, 140, 95)
BLUE = (95, 142, 207)
LIGHT_BLUE = (110, 185, 255)
BLACK = (0, 0, 0)
ENEMY_COLOR = (207, 12, 145)
CYAN = (153, 95, 95)

color_map = {
    0: LIGHT_GRAY,
    1: BROWN,
    2: GREEN,
    3: GRAY,
    4: BLUE,
    5: RED,
}

class Tower():
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

class Enemy():
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


def draw_field():
    for row in range(rows):
        for col in range(cols):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            value = field[row][col]
            
            color = color_map.get(value)
            
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))

            if value == 3:
                pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 1)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

enemy = Enemy()

towers = Tower()

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    enemy.update()
    screen.fill(LIGHT_BLUE)
    draw_field()
    enemy.draw(screen)
    towers.draw(screen, CYAN)
    pygame.display.flip()
    clock.tick(50)

pygame.quit()
sys.exit()