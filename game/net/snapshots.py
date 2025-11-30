# game/net/snapshots.py

from game.world.components import Transform, Facing, AnimationState, Sprite, PlayerTag

def make_snapshot(world, tick: int):
    """
    Build a snapshot of all relevant entities.
    Currently includes:
      - entity id
      - position (x, y)
      - optional pid (from PlayerTag.pid)
      - optional sprite atlas id
      - optional animation clip name
      - optional facing direction
    """
    ents = []

    for eid, comps in world.entities.items():
        tr = comps.get(Transform)
        if tr is None:
            continue

        spr = comps.get(Sprite)
        anim = comps.get(AnimationState)
        face = comps.get(Facing)
        ptag = comps.get(PlayerTag)

        ent_data = {
            "id": eid,
            "x": tr.x,
            "y": tr.y,
        }

        if ptag is not None:
            # try to get player id off tag
            pid = getattr(ptag, "pid", getattr(ptag, "id", None))
            if pid is not None:
                ent_data["pid"] = pid

        if spr is not None:
            ent_data["sprite"] = getattr(spr, "atlas_id", None)

        if anim is not None:
            ent_data["anim"] = getattr(anim, "clip", None)

        if face is not None:
            ent_data["facing"] = getattr(face, "direction", None)

        ents.append(ent_data)

    return {
        "t": 4,          # protocol.MSG_SNAPSHOT
        "tick": tick,
        "entities": ents,
    }


def apply_snapshot(world, snapshot: dict, local_player_id: int | None = None):
    """
    Apply a server snapshot to the local ECS world.
    If local_player_id is given, we won't overwrite that player's transform
    to reduce rubberbanding on the local client.
    """
    from game.world.components import Transform, PlayerTag

    entities = snapshot.get("entities", [])
    for ed in entities:
        eid = ed["id"]

        if eid not in world.entities:
            world.entities[eid] = {}
        comps = world.entities[eid]

        # detect if this entity is the local player
        is_local = False
        if local_player_id is not None:
            ptag = comps.get(PlayerTag)
            if ptag is not None:
                pid = getattr(ptag, "pid", getattr(ptag, "id", None))
                if pid == local_player_id:
                    is_local = True

        # transform
        if not is_local:
            tr = comps.get(Transform)
            if tr is None:
                comps[Transform] = Transform(ed["x"], ed["y"])
            else:
                tr.x = ed["x"]
                tr.y = ed["y"]

        # (If you want, we can later also sync sprite/anim/facing here)

    return snapshot.get("tick", 0)
