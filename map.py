import pygame
import pytmx

class Map():
    def __init__(self, path):
        self.path = path
        self.map_image = self.load_map()
    
    def load_map(self) -> pytmx.TiledMap:
        return pytmx.load_pygame(self.path)


    def draw_map(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        for layer in self.map_image.visible_layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue

            layer_x = int(getattr(layer, "offsetx", 0))
            layer_y = int(getattr(layer, "offsety", 0))

            for tile_x, tile_y, gid in layer:
                if gid == 0:
                    continue

                image = self.map_image.get_tile_image_by_gid(gid)

                if image is None:
                    continue

                cell_x = tile_x * self.map_image.tilewidth
                cell_y = tile_y * self.map_image.tileheight

                x = cell_x
                y = cell_y + self.map_image.tileheight - image.get_height()

                screen.blit(
                    image,
                    (
                        x + layer_x + offset_x,
                        y + layer_y + offset_y
                    )
                )