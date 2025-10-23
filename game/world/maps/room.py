
import pytmx
import pygame

class Room:
    @staticmethod
    def draw_map(surface, tmx_data, entities):
        """
        Draws the room map with Y-sorted tiles and entities.
        Draw order:
          1. floor and abyss layers
          2. Walls + decorations + entities sorted by vertical depth (depth_y)
        """
        # draw static layers first (floor, abyss)
        for layer_name in ("abyss", "floor"):
            try:
                layer = tmx_data.get_layer_by_name(layer_name)
            except ValueError:
                continue
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue

            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    surface.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))

        # get drawable items for walls & decorations
        # this computes per-tile depth using the bottom pixel of the tile
        tile_items = Room.get_sorted_tiles(tmx_data, ("walls", "dec"))

        #compute min depth of all wall/dec tiles so we can draw some entities under entire layer
        #if there are no wall/dec tiles, set to inf so entities won't be forced under.
        if tile_items:
            min_wall_dec_depth = min(depth_y for depth_y, img, pos in tile_items)
        else:
            min_wall_dec_depth = float('inf')

        #cmbine tiles and entities for Y-sorting
        drawables = []

        # Add tile items: (depth_y, kind_rank, image, (x, y))
        for depth_y, img, pos in tile_items:
            drawables.append((depth_y, 0, img, pos))  # kind_rank 0 for tiles

        # determine tile coords occupied by walls/dec
        wall_dec_coords = Room.get_occupied_coords(tmx_data, ("walls", "dec"))

        #add entities: (depth_y, kind_rank, img, (x, y))
        for z, depth_y, eid, img, pos in entities:
            #compute entity feet pixel (bottom of sprite in world pixels)
            feet_y = pos[1] + img.get_height()
            feet_x = pos[0] + img.get_width() // 2

            #convert to tile coords
            tile_x = int(feet_x // tmx_data.tilewidth)
            tile_y = int(feet_y // tmx_data.tileheight)

            # this is where perspective logic is handled
            #if bottom of entity's rect is touching a tile in wall or dec layer, they are drawn under both layers
            if (tile_x, tile_y) in wall_dec_coords:
                # set entity depth to just above the minimum wall/dec tile depth so it sorts before them.
                depth_y_for_sort = int(min_wall_dec_depth) - 1
            else:
                depth_y_for_sort = depth_y

            drawables.append((depth_y_for_sort, 1, img, pos))  # kind_rank 1 for entities

        # sort by vertical depth (and draw tiles before entities at equal depth)
        drawables.sort(key=lambda d: (d[0], d[1]))

        # draw everything in sorted order
        for _, _, img, pos in drawables:
            surface.blit(img, pos)

    @staticmethod
    def get_sorted_tiles(tmx_data, layer_names):
        """
        Returns a list of (depth_y, image, (x, y)) for the given layers.
        depth_y = bottom of the tile image in world pixels.
        """
        items = []

        for layer_name in layer_names:
            try:
                layer = tmx_data.get_layer_by_name(layer_name)
            except ValueError:
                continue

            if not isinstance(layer, pytmx.TiledTileLayer):
                continue

            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if not tile:
                    continue

                draw_x = x * tmx_data.tilewidth
                draw_y = y * tmx_data.tileheight

                #offset for taller tiles
                img_h = tile.get_height()
                draw_y_offset = draw_y + (tmx_data.tileheight - img_h)

                #depth is bottom of tile
                depth_y = draw_y_offset + img_h

                items.append((depth_y, tile, (draw_x, draw_y_offset)))

        #dort so that smaller depth_y are drawn first
        items.sort(key=lambda i: i[0])
        return items


    @staticmethod
    def get_occupied_coords(tmx_data, layer_names):
        """gets the coords of every tile in wall and dec.
        we use them to check if an entity is occupying that tile so perpective is handled accordingly"""
        coords = set()
        for layer_name in layer_names:
            try:
                layer = tmx_data.get_layer_by_name(layer_name)
            except ValueError:
                continue
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue
            for x, y, gid in layer:
                if gid:
                    coords.add((x, y))
        return coords

    @staticmethod
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
