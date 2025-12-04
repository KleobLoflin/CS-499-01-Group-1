# AUTHORED BY: Scott Petty

import os, json, pytmx
from typing import Any, Dict
from game.world.components import Map
from game.world.maps.room import Room
from game.world.maps.map_index import MapInfo
from game.world.maps.utils import *

# function that converts tile coords in the map blueprint to pixel coords for "game_spawns" and "regions" (type: ring, rect, and polygon)
def convert_tile_to_pixel_positions(blueprint: dict, tile_width: int, tile_height: int):
    

    # game spawns ###########################################################################
    gs = blueprint.get("game_spawns", {})

    # convert single-object fields like player_start
    for key in ("player_start",):
        obj = gs.get(key)
        if isinstance(obj, dict) and "tile_pos" in obj:
            tx, ty = obj["tile_pos"]
            obj["pos"] = convert_tiles_to_pixels(int(tx), int(ty), tile_width, tile_height)
            del obj["tile_pos"]
    
    # convert list fields
    for list_key in ("objects", "pickups", "static_enemies", "exits"):
        for entry in gs.get(list_key, []):
            if isinstance(entry, dict) and "tile_pos" in entry:
                tx, ty = entry["tile_pos"]
                entry["pos"] = convert_tiles_to_pixels(int(tx), int(ty), tile_width, tile_height)
                del entry["tile_pos"]

    # regions #######################################################################################
    regs = blueprint.get("regions", {})
    if not isinstance(regs, dict):
        return

    # incase tiles are not square use the smaller dimension for scalar radius
    px_per_tile_scalar = tile_width if tile_width == tile_height else min(tile_width, tile_height)

    for name, r in regs.items():
        if not isinstance(r, dict):
            continue
        rtype = r.get("type")

        if rtype == "ring":
            # center tiles to pixels. radius tiles to pixels
            if "center" in r and isinstance(r["center"], (list, tuple)) and len(r["center"]) == 2:
                tx, ty = r["center"]
                r["center"] = convert_tiles_to_pixels(int(tx), int(ty), tile_width, tile_height)
            if "r_min" in r:
                r["r_min"] = int(r["r_min"]) * px_per_tile_scalar
            if "r_max" in r:
                r["r_max"] = int(r["r_max"]) * px_per_tile_scalar

        elif rtype == "rect":
            # rect tiles to pixels 
            if "x" in r: r["x"] = int(r["x"]) * tile_width + tile_width // 2
            if "y" in r: r["y"] = int(r["y"]) * tile_height + tile_height // 2
            if "w" in r: r["w"] = int(r["w"]) * tile_width 
            if "h" in r: r["h"] = int(r["h"]) * tile_height

        elif rtype == "poly":
            pts = r.get("points")
            if isinstance(pts, list):
                px_pts = []
                for p in pts:
                    if isinstance(p, (list, tuple)) and len(p) == 2:
                        tx, ty = p
                        px_pts.append([int(tx) * tile_width + tile_width // 2, int(ty) * tile_height + tile_height // 2])
                r["points"] = px_pts

def build_Map_component(mi: MapInfo) -> Map:
    tmx = pytmx.util_pygame.load_pygame(mi.tmx_path)
    collisions = Room.load_collision_objects(tmx, layer_name="collisions")

    bp: Dict[str, Any] = {}
    if mi.blueprint_path and os.path.exists(mi.blueprint_path):
        with open(mi.blueprint_path, "r", encoding="utf-8") as f:
            bp = json.load(f)

    # convert tile coords to pixel coords in blueprint
    convert_tile_to_pixel_positions(bp, tmx.tilewidth, tmx.tileheight)
    
    meta = bp.get("meta", {})
    name = os.path.basename(mi.tmx_path)

    # print(f"[Map] {mi.id}: loaded {len(collisions)} collision rects")

    return Map(
        name=name,
        path=mi.tmx_path,
        tmx_data=tmx,
        active=True,                 # factory toggles others off
        id=mi.id,
        collisions=collisions,
        music=meta.get("music"),
        ambience=meta.get("ambience"),
        blueprint=bp
    )
