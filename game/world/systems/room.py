#draws the tmx map to the screen

from pytmx.util_pygame import load_pygame
import pytmx

class Room:
    def draw_map(screen, tmx_data):
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        screen.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))

