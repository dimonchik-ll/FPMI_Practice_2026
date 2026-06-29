import pygame
import sys

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
BLACK = (0, 0, 0)

color_map = {
    0: LIGHT_GRAY,
    1: BROWN,
    2: GREEN,
    3: GRAY,
    4: BLUE,
    5: RED,
}

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

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

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    draw_field()
    pygame.display.flip()

pygame.quit()
sys.exit()