# snapshots.py
from game.world.components import Transform, Facing, AnimationState, Sprite, PlayerTag
# ^ adjust import path if yours are in game.world.components

def make_snapshot(world, tick: int):
    """
    Serialize relevant world state into a snapshot dictionary.
    Includes heroes and enemies.
    """
    heroes = []
    enemies = []

    for eid, comps in world.entities.items():
        tr = comps.get(Transform)
        spr = comps.get(Sprite)
        anim = comps.get(AnimationState)
        face = comps.get(Facing)

        if tr is None:
            continue

        # Check for hero ownership
        owner = comps.get(PlayerTag)
        if owner is not None:
            heroes.append({
                "eid": eid,
                "owner": getattr(owner, "pid", getattr(owner, "id", None)),
                "pos": {"x": tr.x, "y": tr.y},
                "sprite": getattr(spr, "atlas_id", None) if spr else None,
                "anim": getattr(anim, "clip", None) if anim else None,
                "facing": getattr(face, "direction", None) if face else None,
            })
        else:
            enemies.append({
                "eid": eid,
                "kind": getattr(spr, "atlas_id", "unknown") if spr else "unknown",
                "pos": {"x": tr.x, "y": tr.y},
                "sprite": getattr(spr, "atlas_id", None) if spr else None,
                "anim": getattr(anim, "clip", None) if anim else None,
                "facing": getattr(face, "direction", None) if face else None,
            })

    return {
        "tick": tick,
        "heroes": heroes,
        "enemies": enemies,
    }

def apply_snapshot(world, snapshot):
    """
    Apply snapshot to client-side world.
    Overwrites predicted state with server-authoritative data.
    """
    tick = snapshot["tick"]

    # --- HEROES ---
    for pdata in snapshot.get("heroes", []):
        eid = pdata["eid"]
        if eid not in world.entities:
            world.entities[eid] = {}
        comps = world.entities[eid]

        # Position
        from game.world.components import Transform
        tr = comps.get(Transform)
        if tr is None:
            comps[Transform] = Transform(pdata["pos"]["x"], pdata["pos"]["y"])
        else:
            tr.x, tr.y = pdata["pos"]["x"], pdata["pos"]["y"]

    # --- ENEMIES ---
    for edata in snapshot.get("enemies", []):
        eid = edata["eid"]
        if eid not in world.entities:
            world.entities[eid] = {}
        comps = world.entities[eid]

        from game.world.components import Transform
        tr = comps.get(Transform)
        if tr is None:
            comps[Transform] = Transform(edata["pos"]["x"], edata["pos"]["y"])
        else:
            tr.x, tr.y = edata["pos"]["x"], edata["pos"]["y"]


    return tick
