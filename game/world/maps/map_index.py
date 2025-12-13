# AUTHORED BY: Scott Petty

import json
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Iterable
from game.core.paths import resource_path

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
            tmx_path=resource_path(m["tmx_path"]),
            blueprint_path=resource_path(m.get("blueprint_path","")),
            tags=m.get("tags",[]),
            weight=int(m.get("weight",1)),
        )
        for m in data.get("maps", [])
    }

def info(map_id: str) -> MapInfo:
    return REGISTRY[map_id]

def pick(
    require_all: Optional[Iterable[str]] = None,
    require_any: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
) -> MapInfo:
    
    # Weighted random pick from REGISTRY.
    # - require_all: map must contain all of these tags
    # - require_any: map must contain at least one of these tags
    # - exclude:     map must NOT contain any of these tags
    # Uses MapInfo.weight (>=1) for random.choices.
    
    require_all = set(require_all or [])
    require_any = set(require_any or [])
    exclude = set(exclude or [])

    candidates: List[MapInfo] = []
    for mi in REGISTRY.values():
        tags = set(mi.tags)
        if require_all and not require_all.issubset(tags):
            continue
        if require_any and not (tags & require_any):
            continue
        if exclude and (tags & exclude):
            continue
        candidates.append(mi)

    if not candidates:
        raise ValueError(f"No maps match tags (all={list(require_all)}, any={list(require_any)}, exclude={list(exclude)})")

    weights = [max(1, mi.weight) for mi in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]

def pick_many(
    n: int,
    require_all: Optional[Iterable[str]] = None,
    require_any: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
    unique: bool = True,
) -> List[MapInfo]:
    
    # pick N maps with the same filtering. If unique=True, won’t repeat ids.
    
    result: List[MapInfo] = []
    seen = set()
    for _ in range(n):
        mi = pick(require_all=require_all, require_any=require_any, exclude=exclude)
        if unique:
            tries = 0
            while mi.id in seen and tries < 50:
                mi = pick(require_all=require_all, require_any=require_any, exclude=exclude)
                tries += 1
        result.append(mi)
        seen.add(mi.id)
    return result