#AUTHORED BY: Colin Adams
#EDITED BY: Scott Petty
import pytmx
import pygame

#specifies draw order, handles map persepctive between entities and map
class Room:
    @staticmethod
    def visible_tile_bounds(tmx_data, view_left, view_top, view_w, view_h):
        # return (first_tx, first_ty, last_tx, last_ty) clamped to map size.

        tw, th = tmx_data.tilewidth, tmx_data.tileheight
        map_w, map_h = tmx_data.width, tmx_data.height

        first_tx = max(0, int(view_left // tw))
        first_ty = max(0, int(view_top  // th))
        last_tx  = min(map_w - 1, int((view_left + view_w) // tw) + 1)
        last_ty  = min(map_h - 1, int((view_top  + view_h) // th) + 1)
        return first_tx, first_ty, last_tx, last_ty
    
    @staticmethod
    def draw_map_view(surface, tmx_data, entities_world, view_left, view_top, view_w, view_h):
        # culls tiles to the cameras view
        # offsets tiles and entities by (view_left, view_top)
        # entities_world: iterable of (z, depth_y, eid, img, (wx, wy))
        #   - (wx, wy) entities top-left in world pixels

        tw, th = tmx_data.tilewidth, tmx_data.tileheight
        ox = -int(view_left)  
        oy = -int(view_top)  

        # Compute visible tile range once
        first_tx, first_ty, last_tx, last_ty = Room.visible_tile_bounds(
            tmx_data, view_left, view_top, view_w, view_h
        )

        # 1) Draw static layers first (floor, abyss)
        for layer_name in ("abyss", "floor"):
            try:
                layer = tmx_data.get_layer_by_name(layer_name)
            except ValueError:
                continue
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue

            # Iterate only visible tiles
            for x in range(first_tx, last_tx + 1):
                for y in range(first_ty, last_ty + 1):
                    # pytmx lets you get gid with layer.data[y][x] 
                    try:
                        gid = layer.data[y][x]
                    except Exception:
                        gid = 0
                    if not gid:
                        continue
                    tile = tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        surface.blit(tile, (x * tw + ox, y * th + oy))

        # 2) Build y-sorted list for wall/dec tiles
        tile_items = Room.get_sorted_tiles_view(tmx_data, ("walls", "dec"),
                                                first_tx, first_ty, last_tx, last_ty)

        # Compute min depth of wall/dec tiles; if none, set INF so entities won't be forced under
        if tile_items:
            min_wall_dec_depth = min(depth_y for depth_y, img, pos_screen, _pos_world in tile_items)
        else:
            min_wall_dec_depth = float('inf')

        # 3) Collect drawables (tiles + entities) for unified y-sort.
        drawables = []

        # Add tiles: (depth_y_world, kind_rank, image, (sx, sy))
        for depth_y, img, _pos_screen, pos_world in tile_items:
            wx, wy = pos_world
            sx = int(wx + ox)
            sy = int(wy + oy)
            drawables.append((depth_y, 0, img, (sx, sy)))

        # Determine tile coords occupied by walls/dec for perspective rule 
        wall_dec_coords = Room.get_occupied_coords(tmx_data, ("walls", "dec"))

        # 4) Add entities, applying perspective rule against wall/dec tiles.
        # 4) Add entities, applying perspective rule against wall/dec tiles.
        # entities_world now contains: (z, depth_y, eid, img, (wx, wy), tr_x)
        for z, depth_y, eid, img, pos_world, tr_x in entities_world:
            wx, wy = pos_world  # world top-left of sprite (for drawing)
            # Use transform values for feet: tr_x (world x of "feet/anchor") and depth_y (world y).
            feet_x = tr_x
            feet_y = depth_y

            tile_x = int(feet_x // tw)
            tile_y = int(feet_y // th)

            # If the feet are on a wall/dec tile, draw under that whole layer.
            if (tile_x, tile_y) in wall_dec_coords:
                depth_y_for_sort = int(min_wall_dec_depth) - 1
            else:
                depth_y_for_sort = depth_y

            # Convert world -> screen with camera offset
            sx = int(wx + ox)
            sy = int(wy + oy)

            drawables.append((depth_y_for_sort, 1, img, (sx, sy)))  # kind_rank 1 for entities


        # 5) Sort & draw
        drawables.sort(key=lambda d: (d[0], d[1]))
        for _, _, img, pos in drawables:
            surface.blit(img, pos)

    @staticmethod
    def draw_map(surface, tmx_data, entities_world):
        # backwards compatible with old system
        # uses draw_map_view with a full-view rect anchored at (0,0)
        view_left = 0
        view_top = 0
        view_w = tmx_data.width * tmx_data.tilewidth
        view_h = tmx_data.height * tmx_data.tileheight
        Room.draw_map_view(surface, tmx_data, entities_world, view_left, view_top, view_w, view_h)

    @staticmethod
    def get_sorted_tiles_view(tmx_data, layer_names, first_tx, first_ty, last_tx, last_ty):
        
        # Returns a list of (depth_y_world, image, (sx, sy), (wx, wy)) for the given layers,
        # culled to the visible tile range. Screen position is computed assuming a camera
        # offset of (view_left, view_top). Caller should pass in ox/oy by subtracting
        # view_left/view_top before blitting.
        
        items = []
        tw, th = tmx_data.tilewidth, tmx_data.tileheight

        for layer_name in layer_names:
            try:
                layer = tmx_data.get_layer_by_name(layer_name)
            except ValueError:
                continue

            if not isinstance(layer, pytmx.TiledTileLayer):
                continue

            for x in range(first_tx, last_tx + 1):
                for y in range(first_ty, last_ty + 1):
                    try:
                        gid = layer.data[y][x]
                    except Exception:
                        gid = 0
                    if not gid:
                        continue

                    tile = tmx_data.get_tile_image_by_gid(gid)
                    if not tile:
                        continue

                    # world top-left of this tile cell
                    draw_x_world = x * tw
                    draw_y_world = y * th

                    # Offset for taller tiles
                    img_h = tile.get_height()
                    draw_y_offset_world = draw_y_world + (th - img_h)

                    # Depth is world bottom pixel of the tile
                    depth_y_world = draw_y_offset_world + img_h

                    # return both world pos and a placeholder for screen pos
                    items.append(
                        (depth_y_world, tile, (draw_x_world, draw_y_offset_world), (draw_x_world, draw_y_offset_world))
                    )

        # Sort by world depth
        items.sort(key=lambda i: i[0])
        return items

    @staticmethod
    def get_sorted_tiles(tmx_data, layer_names):
        # legacy helper for compatability
        # not used in draw_map_view
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
            for y in range(tmx_data.height):
                for x in range(tmx_data.width):
                    try:
                        gid = layer.data[y][x]
                    except Exception:
                        gid = 0
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
