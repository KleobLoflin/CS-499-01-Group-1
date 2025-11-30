# game/net/snapshots.py
#
# Building and applying world snapshots.
# Host: collects players, enemies, and pickups into a serializable dict.
# Client: applies that dict to proxy entities (RemoteEntity) for enemies/pickups.

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

from game.world.components import (
    PlayerTag,
    Owner,
    Transform,
    Facing,
    AnimationState,
    Sprite,
    Life,
    AI,
    Pickup,
    RemoteEntity,
    ActiveMapId,
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
class EnemySnapshot:
    id: int              # host-side entity id
    x: float
    y: float
    facing: str
    clip: str
    frame: int
    hp: float
    atlas_id: str        # which sprite atlas to use


@dataclass
class PickupSnapshot:
    id: int
    x: float
    y: float
    kind: str
    atlas_id: str


@dataclass
class WorldSnapshot:
    tick: int
    map_id: Optional[str]
    players: List[PlayerSnapshot]
    enemies: List[EnemySnapshot]
    pickups: List[PickupSnapshot]


# host-side ###############################################################

# gets current presentation state for players, enemies, and pickups into a serializable dict
# called on the Host
# map geometry not serialized because both host and clients load the same TMX map blueprint
def build_world_snapshot(world, tick: int) -> Dict[str, Any]:
    # Active map id 
    map_id: Optional[str] = None
    for _eid, comps in world.query(ActiveMapId):
        map_id = comps[ActiveMapId].id
        break

    # Players
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

    # Enemies: any AI+Life entity that is not tagged as a Player
    enemies: List[EnemySnapshot] = []
    for eid, comps in world.query(AI, Life, Transform, Facing, AnimationState, Sprite):
        if PlayerTag in comps:
            continue  # skip any weird player+AI hybrids

        tr: Transform = comps[Transform]
        facing: Facing = comps[Facing]
        anim: AnimationState = comps[AnimationState]
        life: Life = comps[Life]
        spr: Sprite = comps[Sprite]

        enemies.append(EnemySnapshot(
            id=eid,
            x=tr.x,
            y=tr.y,
            facing=facing.direction,
            clip=anim.clip,
            frame=anim.frame,
            hp=life.hp,
            atlas_id=spr.atlas_id,
        ))

    # Pickups
    pickups: List[PickupSnapshot] = []
    for eid, comps in world.query(Pickup, Transform, Sprite):
        tr: Transform = comps[Transform]
        p: Pickup = comps[Pickup]
        spr: Sprite = comps[Sprite]

        pickups.append(PickupSnapshot(
            id=eid,
            x=tr.x,
            y=tr.y,
            kind=p.kind,
            atlas_id=spr.atlas_id,
        ))

    snapshot = WorldSnapshot(
        tick=tick,
        map_id=map_id,
        players=players,
        enemies=enemies,
        pickups=pickups,
    )

    return {
        "tick": snapshot.tick,
        "map_id": snapshot.map_id,
        "players": [asdict(p) for p in snapshot.players],
        "enemies": [asdict(e) for e in snapshot.enemies],
        "pickups": [asdict(p) for p in snapshot.pickups],
    }


# client-side utilities ################################################

#  Look up or create a client-side proxy entity representing an enemy owned by the host
# identified by remote_id
def _find_or_create_remote_enemy(world, remote_id: int, atlas_id: str):
    # see if we already have this one
    for _eid, comps in world.query(RemoteEntity, Transform, Facing, AnimationState, Sprite, Life):
        rem: RemoteEntity = comps[RemoteEntity]
        if rem.category == "enemy" and rem.remote_id == remote_id:
            return comps

    # else create a new proxy
    e = world.new_entity()
    comps = world.components_of(e)
    comps[RemoteEntity] = RemoteEntity(remote_id=remote_id, category="enemy")
    comps[Transform] = Transform(x=0.0, y=0.0)
    comps[Facing] = Facing()
    comps[AnimationState] = AnimationState()
    comps[Sprite] = Sprite(atlas_id=atlas_id)
    comps[Life] = Life()
    return comps

# Look up or create a client-side proxy entity representing a pickup owned by the host.
def _find_or_create_remote_pickup(world, remote_id: int, atlas_id: str, kind: str):
    for _eid, comps in world.query(RemoteEntity, Transform, Sprite, Pickup):
        rem: RemoteEntity = comps[RemoteEntity]
        if rem.category == "pickup" and rem.remote_id == remote_id:
            return comps

    e = world.new_entity()
    comps = world.components_of(e)
    comps[RemoteEntity] = RemoteEntity(remote_id=remote_id, category="pickup")
    comps[Transform] = Transform(x=0.0, y=0.0)
    comps[Sprite] = Sprite(atlas_id=atlas_id)
    comps[Pickup] = Pickup(kind=kind)
    return comps

# remove any RemoteEntity entities of the given category that are no longer in the latest snapshot
def _cleanup_remote_category(world, category: str, ids_in_snapshot: set[int]) -> None:
    to_delete: List[int] = []
    for eid, comps in world.query(RemoteEntity):
        rem: RemoteEntity = comps[RemoteEntity]
        if rem.category == category and rem.remote_id not in ids_in_snapshot:
            to_delete.append(eid)

    for eid in to_delete:
        world.delete_entity(eid)


# client-side main entry ##############################################################

# Apply a snapshot message on the client
def apply_world_snapshot(world, msg: Dict[str, Any], my_peer_id: str) -> None:
    # Map id is informational. actual map geometry should be loaded by the scene.

    # Players
    players_data = msg.get("players", [])

    for pdata in players_data:
        peer_id = pdata.get("peer_id")
        if peer_id is None:
            continue
        if peer_id == my_peer_id:
            # Don't stomp local-controlled player here.
            continue

        found = False
        for _eid, comps in world.query(PlayerTag, Owner, Transform, Facing, AnimationState):
            owner: Owner = comps[Owner]
            if owner.peer_id == peer_id:
                tr: Transform = comps[Transform]
                facing: Facing = comps[Facing]
                anim: AnimationState = comps[AnimationState]

                tr.x = float(pdata.get("x", tr.x))
                tr.y = float(pdata.get("y", tr.y))
                facing.direction = pdata.get("facing", facing.direction)
                anim.clip = pdata.get("clip", anim.clip)
                anim.frame = int(pdata.get("frame", anim.frame))
                anim.changed = True
                found = True
                break

        if not found:
            pass

    # Enemies 
    enemies_data = msg.get("enemies", [])
    enemy_ids_in_snapshot: set[int] = set()

    for edata in enemies_data:
        try:
            rid = int(edata.get("id"))
        except (TypeError, ValueError):
            continue
        enemy_ids_in_snapshot.add(rid)

        atlas_id = edata.get("atlas_id", "enemy.chort")
        comps = _find_or_create_remote_enemy(world, rid, atlas_id)

        tr: Transform = comps[Transform]
        facing: Facing = comps[Facing]
        anim: AnimationState = comps[AnimationState]
        life: Life = comps[Life]

        tr.x = float(edata.get("x", tr.x))
        tr.y = float(edata.get("y", tr.y))
        facing.direction = edata.get("facing", facing.direction)
        anim.clip = edata.get("clip", anim.clip)
        anim.frame = int(edata.get("frame", anim.frame))
        anim.changed = True
        life.hp = float(edata.get("hp", life.hp))

    _cleanup_remote_category(world, "enemy", enemy_ids_in_snapshot)

    # Pickups
    pickups_data = msg.get("pickups", [])
    pickup_ids_in_snapshot: set[int] = set()

    for pdata in pickups_data:
        try:
            rid = int(pdata.get("id"))
        except (TypeError, ValueError):
            continue
        pickup_ids_in_snapshot.add(rid)

        kind = pdata.get("kind", "potion_health")
        atlas_id = pdata.get("atlas_id", kind)
        comps = _find_or_create_remote_pickup(world, rid, atlas_id, kind)

        tr: Transform = comps[Transform]
        tr.x = float(pdata.get("x", tr.x))
        tr.y = float(pdata.get("y", tr.y))

    _cleanup_remote_category(world, "pickup", pickup_ids_in_snapshot)
