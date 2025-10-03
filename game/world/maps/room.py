#draws the tmx map to the screen

from pytmx.util_pygame import load_pygame
import pytmx
import pygame

class Room:
    def draw_map(screen, tmx_data):
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        screen.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))
    
    def load_collision_objects(tmx_data, layer_name="collisions"):
        #Load collision rectangles from an object layer
        rects = []
        try:
            layer = tmx_data.get_layer_by_name(layer_name)
        except ValueError:
            print(f"[Room] No layer named '{layer_name}' found in map.")
            return rects

        for obj in layer:
            # Only handle rectangle objects
            if hasattr(obj, 'width') and hasattr(obj, 'height'):
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                rects.append(rect)
        
        return rects
