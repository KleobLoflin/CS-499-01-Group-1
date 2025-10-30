def map_world_bounds(tmx_data):
    # Return (x, y, w, h) bounds in world pixels for a Tiled map.
    w = tmx_data.width * tmx_data.tilewidth
    h = tmx_data.height * tmx_data.tileheight
    return (0, 0, w, h)