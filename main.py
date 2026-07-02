import pygame
import sys

from pygame import Vector2

from Entities.Enemies.goblin import Goblin
from Entities.Movements.path_movement import PathMovement
from Map.time_map import TileMap
from Navigation.path_provider import PathProvider
from constants import *

pygame.init()

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))


tile_map = TileMap(field)

path_provider = PathProvider(tile_map)
path = path_provider.build_path()

path_movement = PathMovement(path)

enemy = Goblin(Vector2(3* TILE_SIZE,2 * TILE_SIZE), path_movement)

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    delta_time = clock.tick(50) / 1000

    enemy.update(delta_time)

    screen.fill(LIGHT_BLUE)

    tile_map.draw(screen)
    enemy.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()