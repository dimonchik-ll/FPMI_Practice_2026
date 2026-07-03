import pygame
import sys

from constants import *
from map import Map
from Entities.Enemies.enemy import Enemy
from Entities.Towers.tower import Tower


def get_building_gid_at_mouse(game_map, mouse_x, mouse_y):
    buildings_layer = game_map.map_image.get_layer_by_name("Buildings")

    for tile_x, tile_y, gid in buildings_layer:
        if gid == 0:
            continue

        image = game_map.map_image.get_tile_image_by_gid(gid)

        if image is None:
            continue

        cell_x = tile_x * game_map.map_image.tilewidth
        cell_y = tile_y * game_map.map_image.tileheight

        image_x = cell_x
        image_y = cell_y + game_map.map_image.tileheight - image.get_height()

        image_rect = pygame.Rect(
            image_x,
            image_y,
            image.get_width(),
            image.get_height()
        )

        if image_rect.collidepoint(mouse_x, mouse_y):
            return gid

    return 0

def draw_build_menu(screen):
    menu_rect = pygame.Rect(300, 200, 360, 170)

    pygame.draw.rect(screen, (45, 45, 45), menu_rect)
    pygame.draw.rect(screen, (220, 220, 220), menu_rect, 3)

    font = pygame.font.Font(None, 34)

    screen.blit(
        font.render("BUILD MENU", True, (255, 255, 255)),
        (menu_rect.x + 105, menu_rect.y + 20)
    )

    screen.blit(
        font.render("1 - Build tower", True, (255, 255, 255)),
        (menu_rect.x + 70, menu_rect.y + 75)
    )

    screen.blit(
        font.render("ESC - Close", True, (255, 255, 255)),
        (menu_rect.x + 70, menu_rect.y + 115)
    )


pygame.init()

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Tower Defense Map")

game_map = Map("maps/demo.tmx")

clock = pygame.time.Clock()
enemies = []
towers = []

spawn_timer = 0.0
spawn_delay = 1.5

build_menu_open = False
selected_build_position = None

build_menu_open = False
running = True

while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                build_menu_open = False
                selected_build_position = None
                pygame.display.set_caption("Tower Defense Map")

            if event.key == pygame.K_1 and build_menu_open:
                x, y = selected_build_position

                towers.append(
                    Tower(
                        x + game_map.map_image.tilewidth // 2,
                        y + game_map.map_image.tileheight // 2
                    )
                )

                build_menu_open = False
                selected_build_position = None
                pygame.display.set_caption("Tower Defense Map")

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos

            gid = get_building_gid_at_mouse(game_map, mouse_x, mouse_y)

            if gid != 0:
                tile_x = mouse_x // game_map.map_image.tilewidth
                tile_y = mouse_y // game_map.map_image.tileheight

                selected_build_position = (
                    tile_x * game_map.map_image.tilewidth,
                    tile_y * game_map.map_image.tileheight
                )

                build_menu_open = True
                pygame.display.set_caption("BUILD MENU")

    spawn_timer += dt

    if spawn_timer >= spawn_delay:
        enemies.append(Enemy(PATH))
        spawn_timer = 0.0

    for enemy in enemies[:]:
        enemy.update(dt)

        if not enemy.alive:
            enemies.remove(enemy)

    for tower in towers:
        tower.update(dt, enemies)

    screen.fill((0, 0, 0))

    game_map.draw_map(screen)

    for tower in towers:
        tower.draw(screen)

    for enemy in enemies:
        enemy.draw(screen)

    if build_menu_open:
        draw_build_menu(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()