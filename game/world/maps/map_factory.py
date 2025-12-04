# AUTHORED BY: Scott Petty

from game.world.maps.map_index import info, REGISTRY
from game.world.maps.map_blueprint import build_Map_component
from game.world.components import Map, ActiveMapId, MapSpawnState

def get_or_make_singleton(world, Comp, **kwargs):
    for _, comps in world.query(Comp):
        return comps[Comp]
    e = world.new_entity()
    inst = Comp(**kwargs) if kwargs else Comp()  # type: ignore
    world.add(e, inst)
    return inst

def resolve_map_hint_to_id(hint: str) -> str | None:
    # accepts registry id or a tmx file name
    if hint in REGISTRY:
        return hint
    h = hint.lower()
    if h.endswith(".tmx"):
        for mid, mi in REGISTRY.items():
            if mi.tmx_path.lower().endswith(h):
                return mid
    return None

def create_or_activate(world, map_id: str) -> int:
    # Activate existing Map entity for map_id or build a new one. Returns the Map entity id.
    # Deactivate others, and see if already present
    existing = None
    for eid, comps in world.query(Map):
        m = comps[Map]
        if m.id == map_id:
            existing = eid
        m.active = False

    if existing is not None:
        world.components_of(existing)[Map].active = True
        map_eid = existing
    else:
        mi = info(map_id)
        map_eid = world.new_entity()
        world.add(map_eid, build_Map_component(mi))
        world.add(map_eid, MapSpawnState())

    # set ActiveMapId singleton
    am = get_or_make_singleton(world, ActiveMapId, id=map_id)
    am.id = map_id
    return map_eid
