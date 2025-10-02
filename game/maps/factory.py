from dataclasses import dataclass
from typing import Dict, Any
import json, os
import pytmx
from game.world.systems.room import Room
from game.maps.registry import MapInfo

@dataclass
class MapInstance:
    id: str
    tmx: object
    collisions: list
    blueprint: Dict[str, Any]
    name: str
    music: str | None
    ambience: str | None

class MapFactory:
    def __init__(self, catalog: Dict[str, MapInfo]):
        self.catalog = catalog
    
    def create(self, map_id: str) -> MapInstance:
        info = self.catalog[map_id]
        tmx = pytmx.util_pygame.load_pygame(info.tmx_path)
        collisions = Room.load_collision_objects(tmx, layer_name="collisions")

        bp: Dict[str, Any] = {}
        if os.path.exists(info.blueprint_path):
            with open(info.blueprint_path, "r", encoding="utf-8") as f:
                bp = json.load(f)

        meta = bp.get("meta", {})
        name = meta.get("name", info.id)
        music = meta.get("music")
        ambience = meta.get("ambience")

        return MapInstance(
            id=info.id, tmx=tmx, collisions=collisions, blueprint=bp, name=name, music=music, ambience=ambience
        )