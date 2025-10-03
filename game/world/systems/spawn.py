# game/world/systems/spawn.py
from game.world.components import (
    Map, OnMap, MapSpawnState, ActiveMapId, SpawnPolicy,
    WorldObject, Pickup, Transform, Intent, Movement, Facing
)
from game.world.actors.enemy_factory import create as create_enemy
from game.world.actors.hero_factory import create as create_hero
from game.world.spawn.regions import sample_point

class SpawnSystem:
    
    # If policy.run_title_spawns: consumes blueprint['title_spawns'] once per map.
    # If policy.run_game_spawns:  consumes blueprint['game_spawns']  once per map.
    
    def update(self, world, dt: float):
        policy = _get_policy(world)
        active_id = _active_map_id(world)
        if not active_id:
            return
        map_eid, mp = _map_by_id(world, active_id)
        if not mp or not mp.blueprint:
            return

        state = _ensure_map_state(world, map_eid)

        # Title spawns
        if policy.run_title_spawns and not getattr(state, "did_title_spawns", False):
            _run_title_spawns(world, mp, active_id)
            state.did_title_spawns = True  # add this attr lazily for backward-compat

        # Gameplay spawns
        if policy.run_game_spawns and not state.did_initial_spawns:
            _run_game_spawns(world, mp, active_id, policy)
            state.did_initial_spawns = True


def _run_title_spawns(world, mp: Map, active_id: str):
    entries = mp.blueprint.get("title_spawns") or []
    regions = mp.blueprint.get("regions") or {}
    if not entries:
        # Optional default: a handful in 'center'
        entries = [{"kind":"enemy","enemy_type":"chort","count":5,"region":"center"}]
    for e in entries:
        if e.get("kind") != "enemy":
            continue
        et = e.get("enemy_type", "chort")
        cnt = int(e.get("count", 1))
        pts = e.get("points") or []
        reg = e.get("region", "center")
        for i in range(cnt):
            pos = tuple(pts[i]) if i < len(pts) else sample_point(regions, reg)
            eid = create_enemy(world, kind=et, pos=pos)
            _ensure_basics(world, eid)
            world.add(eid, OnMap(id=active_id))


def _run_game_spawns(world, mp: Map, active_id: str, policy: SpawnPolicy):
    gs = mp.blueprint.get("game_spawns") or {}

    # 1) Player start 
    if policy.spawn_player and "player_start" in gs:
        px, py = gs["player_start"].get("pos", [128, 192])
        pid = create_hero(world, pos=(px, py))
        _ensure_basics(world, pid)
        world.add(pid, OnMap(id=active_id))

    # 2) Objects
    if policy.spawn_objects:
        for o in gs.get("objects", []):
            kind = o.get("type", "crate")
            ox, oy = o.get("pos", [0, 0])
            eid = world.new_entity()
            world.add(eid, WorldObject(kind=kind))
            world.add(eid, Transform(float(ox), float(oy)))
            world.add(eid, OnMap(id=active_id))

    # 3) Pickups
    if policy.spawn_pickups:
        for p in gs.get("pickups", []):
            kind = p.get("type", "potion_small")
            px, py = p.get("pos", [0, 0])
            eid = world.new_entity()
            world.add(eid, Pickup(kind=kind))
            world.add(eid, Transform(float(px), float(py)))
            world.add(eid, OnMap(id=active_id))

    # 4) Static enemies
    if policy.spawn_static_enemies:
        for e in gs.get("static_enemies", []):
            et = e.get("type", "slime")
            ex, ey = e.get("pos", [0, 0])
            eid = create_enemy(world, kind=et, pos=(ex, ey))
            _ensure_basics(world, eid)
            world.add(eid, OnMap(id=active_id))

    # 5) Exits 
    # ...


# helpers ########################################################################

def _get_policy(world) -> SpawnPolicy:
    for _, comps in world.query(SpawnPolicy):
        return comps[SpawnPolicy]
    return SpawnPolicy()  # safe defaults

def _active_map_id(world):
    for _, comps in world.query(ActiveMapId):
        return comps[ActiveMapId].id
    return None

def _map_by_id(world, map_id: str):
    for eid, comps in world.query(Map):
        if comps[Map].id == map_id:
            return eid, comps[Map]
    return None, None

def _ensure_map_state(world, map_eid):
    comps = world.components_of(map_eid)
    st = comps.get(MapSpawnState)
    if st is None:
        st = MapSpawnState()
        world.add(map_eid, st)
    return st

def _ensure_basics(world, eid):
    if world.get(eid, Intent) is None:   world.add(eid, Intent())
    if world.get(eid, Movement) is None: world.add(eid, Movement(speed=50))
    if world.get(eid, Facing) is None:   world.add(eid, Facing(direction="down"))
