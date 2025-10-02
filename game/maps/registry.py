# resource loader for map information for use with map_registry.json
# has a pick_random function that picks a random map based on requested tags and a weight value associated with each map

from dataclasses import dataclass
from typing import Dict, List, Optional
import json, os, random

@dataclass(frozen=True)
class MapInfo:
    id: str
    tmx_path: str
    blueprint_path: str
    tags: List[str]
    weight: int = 1

def load_registry(path: str) -> Dict[str, MapInfo]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out: Dict[str, MapInfo] = {}
    for m in data.get("maps", []):
        info = MapInfo(
            id=m["id"],
            tmx_path=m["tmx_path"],
            blueprint_path=m.get("blueprint_path"),
            tags=m.get("tags", []),
            weight=int(m.get("weight", 1)),
        )
        out[info.id] = info
    return out

def pick_random(catalog: Dict[str, MapInfo], *, require_tags: Optional[List[str]] = None) -> MapInfo:
    # filter by requested tags if provided
    candidates = list(catalog.values())
    if require_tags:
        candidates = [mi for mi in candidates if all(t in mi.tags for t in require_tags)]
    # weighted choice
    weights = [max(1, mi.weight) for mi in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]
