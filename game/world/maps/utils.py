def map_world_bounds(tmx_data):
    # Return (x, y, w, h) bounds in world pixels for a Tiled map.
    w = tmx_data.width * tmx_data.tilewidth
    h = tmx_data.height * tmx_data.tileheight
    return (0, 0, w, h)

def convert_tiles_to_pixels(x_tile: int, y_tile: int, tile_width: int, tile_height: int) -> tuple[int, int]:
    x = x_tile * tile_width + tile_width // 2
    y = y_tile * tile_height + tile_height // 2
    return x, y