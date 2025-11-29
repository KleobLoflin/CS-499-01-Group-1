# Building and applying world snapshots.

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from game.world.components import (
    PlayerTag,
    Owner,
    Transform,
    Facing,
    AnimationState,
)


@dataclass
class PlayerSnapshot:
    peer_id: str
    x: float
    y: float
    facing: str
    clip: str
    frame: int


@dataclass
class WorldSnapshot:
    tick: int
    players: List[PlayerSnapshot]


# host-side

def build_world_snapshot(world, tick: int) -> Dict[str, Any]:
    """
    Collects current player presentation state into a serializable dict.
    Called on the HOST.
    """
    players: List[PlayerSnapshot] = []

    for _eid, comps in world.query(PlayerTag, Owner, Transform, Facing, AnimationState):
        owner: Owner = comps[Owner]
        tr: Transform = comps[Transform]
        facing: Facing = comps[Facing]
        anim: AnimationState = comps[AnimationState]

        players.append(PlayerSnapshot(
            peer_id=owner.peer_id,
            x=tr.x,
            y=tr.y,
            facing=facing.direction,
            clip=anim.clip,
            frame=anim.frame,
        ))

    snapshot = WorldSnapshot(tick=tick, players=players)
    return {
        "tick": snapshot.tick,
        "players": [asdict(p) for p in snapshot.players],
    }


# client-side

def _find_or_create_remote_player(world, peer_id: str) -> Dict[type, Any]:
    """
    Returns the components dict for the entity representing this peer on the CLIENT.
    If it does not exist yet, this will create a simple proxy entity.
    NOTE: Local player (matching my_peer_id) is *not* created via this function.
    """
    from game.world.components import (
        PlayerTag,
        Owner,
        Transform,
        Facing,
        AnimationState,
        Sprite,
    )

    # Try to find an existing player with this owner.
    for eid, comps in world.query(PlayerTag, Owner, Transform, Facing, AnimationState):
        owner: Owner = comps[Owner]
        if owner.peer_id == peer_id:
            return comps

    # Otherwise create a minimal remote player proxy.
    e = world.new_entity()
    comps = world.components_of(e)
    comps[PlayerTag] = PlayerTag()
    comps[Owner] = Owner(peer_id=peer_id)
    comps[Transform] = Transform(x=0.0, y=0.0)
    comps[Facing] = Facing()
    comps[AnimationState] = AnimationState()
    # Presentation: generic sprite
    comps[Sprite] = Sprite(atlas_id="hero.knight_blue")
    return comps


def apply_world_snapshot(world, msg: Dict[str, Any], my_peer_id: str) -> None:
    """
    Apply a snapshot message on the CLIENT.
    For now this directly overwrites positions; later we can extend this
    to interpolate between snapshots and perform client-side prediction/
    reconciliation for the local player.
    """
    players_data = msg.get("players", [])

    for pdata in players_data:
        peer_id = pdata.get("peer_id")
        if peer_id is None:
            continue

        # Don't overwrite local-controlled player
        if peer_id == my_peer_id:
            continue

        comps = _find_or_create_remote_player(world, peer_id)

        tr: Transform = comps[Transform]
        facing: Facing = comps[Facing]
        anim: AnimationState = comps[AnimationState]

        tr.x = float(pdata.get("x", tr.x))
        tr.y = float(pdata.get("y", tr.y))
        facing.direction = pdata.get("facing", facing.direction)
        anim.clip = pdata.get("clip", anim.clip)
        anim.frame = int(pdata.get("frame", anim.frame))
        anim.changed = True  # force animation system to resync
