import json
from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class MapInfo:
    id: str
    tmx_path: str
    blueprint_path: str
    tags: List[str]
    weight: int = 1

REGISTRY: Dict[str, MapInfo] = {}

def load_registry(path: str):
    global REGISTRY
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    REGISTRY = {
        m["id"]: MapInfo(
            id=m["id"],
            tmx_path=m["tmx_path"],
            blueprint_path=m.get("blueprint_path",""),
            tags=m.get("tags",[]),
            weight=int(m.get("weight",1)),
        )
        for m in data.get("maps", [])
    }

def info(map_id: str) -> MapInfo:
    return REGISTRY[map_id]
