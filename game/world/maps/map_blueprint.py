import os, json, pytmx
from typing import Any, Dict
from game.world.components import Map
from game.world.systems.room import Room
from game.world.maps.map_index import MapInfo

def build_Map_component(mi: MapInfo) -> Map:
    tmx = pytmx.util_pygame.load_pygame(mi.tmx_path)
    collisions = Room.load_collision_objects(tmx, layer_name="collisions")

    bp: Dict[str, Any] = {}
    if mi.blueprint_path and os.path.exists(mi.blueprint_path):
        with open(mi.blueprint_path, "r", encoding="utf-8") as f:
            bp = json.load(f)

    # 
    meta = bp.get("meta", {})
    name = os.path.basename(mi.tmx_path)

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
