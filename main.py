import pygame
import sys
from constants import *
from Entities.Enemies.enemy import Enemy
from Entities.Towers.tower import Tower
from Entities.entity_base import EntityBase 
from map import Map

pygame.init()

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

entities = []

enemy = Enemy()
entities.append(enemy)

towers = Tower()
entities.append(towers)

map = Map("maps/demo.tmx")

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    map.draw_map(screen)
    pygame.display.flip()
    clock.tick(50)

pygame.quit()
sys.exit()