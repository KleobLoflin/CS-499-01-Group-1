# AUTHORED BY: Scott Petty, Cole Herzog
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
    OnMap,
    SoundRequest,
)

from game.world.maps.map_factory import create_or_activate, resolve_map_hint_to_id

# helper to map atlas_id to enemy size
def _infer_enemy_size_from_atlas_id(atlas_id: str) -> str:
    aid = atlas_id.lower()

    # Boss / huge
    if "boss" in aid:
        return "big"

    # Bigger regular monsters like big zombie
    if "big_zombie" in aid or "zombie_big" in aid or "brute" in aid:
        return "medium"

    # Small enemies like chort
    if "chort" in aid:
        return "small"

    # Tiny enemies like goblin
    if "goblin" in aid or "tiny" in aid:
        return "tiny"

    # Fallback
    return "small"

@dataclass
class PlayerSnapshot:
    peer_id: str
    x: float
    y: float
    facing: str
    clip: str
    frame: int
    hp: float
    map_id: Optional[str] = None


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
    map_id: Optional[str] = None


@dataclass
class PickupSnapshot:
    id: int
    x: float
    y: float
    kind: str
    atlas_id: str
    map_id: Optional[str] = None


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
    # Host's currently active map id 
    host_map_id: Optional[str] = None
    for _eid, comps in world.query(ActiveMapId):
        host_map_id = comps[ActiveMapId].id
        break

    # Players
    players: List[PlayerSnapshot] = []
    for _eid, comps in world.query(PlayerTag, Owner, Transform, Facing, AnimationState, Life):
        owner: Owner = comps[Owner]
        tr: Transform = comps[Transform]
        facing: Facing = comps[Facing]
        anim: AnimationState = comps[AnimationState]
        life: Life = comps[Life]
        om: OnMap | None = world.get(_eid, OnMap)

        players.append(PlayerSnapshot(
            peer_id=owner.peer_id,
            x=tr.x,
            y=tr.y,
            facing=facing.direction,
            clip=anim.clip,
            frame=anim.frame,
            hp=life.hp,
            map_id=getattr(om, "id", None),
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
        om: OnMap | None = world.get(eid, OnMap)

        enemies.append(EnemySnapshot(
            id=eid,
            x=tr.x,
            y=tr.y,
            facing=facing.direction,
            clip=anim.clip,
            frame=anim.frame,
            hp=life.hp,
            atlas_id=spr.atlas_id,
            map_id=getattr(om, "id", None),
        ))

    # Pickups
    pickups: List[PickupSnapshot] = []
    for eid, comps in world.query(Pickup, Transform, Sprite):
        tr: Transform = comps[Transform]
        p: Pickup = comps[Pickup]
        spr: Sprite = comps[Sprite]
        om: OnMap | None = world.get(eid, OnMap)

        pickups.append(PickupSnapshot(
            id=eid,
            x=tr.x,
            y=tr.y,
            kind=p.kind,
            atlas_id=spr.atlas_id,
            map_id=getattr(om, "id", None),
        ))

    snapshot = WorldSnapshot(
        tick=tick,
        map_id=host_map_id,
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

    # enemy aggro sfx
    size = _infer_enemy_size_from_atlas_id(atlas_id)
    comps[SoundRequest] = SoundRequest(
        event="enemy_aggro",
        subtype=size,
        global_event=False,
    )

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

    # Players #############################
    players_data = msg.get("players", [])

    for pdata in players_data:
        peer_id = pdata.get("peer_id")
        if peer_id is None:
            continue
        
        snapshot_map_id = pdata.get("map_id")

        for eid, comps in world.query(PlayerTag, Owner, Transform, Facing, AnimationState, Life):
            owner: Owner = comps[Owner]
            if owner.peer_id != peer_id:
                continue
            
            tr: Transform = comps[Transform]
            facing: Facing = comps[Facing]
            anim: AnimationState = comps[AnimationState]
            life: Life = comps[Life]
            
            # record previous HP
            old_hp = life.hp

            # previous map id for this entity
            prev_map_id: Optional[str] = None
            om_existing: OnMap | None = world.get(eid, OnMap)
            if om_existing is not None:
                prev_map_id = om_existing.id

            # update OnMap from snapshot
            if isinstance(snapshot_map_id, str):
                if om_existing is not None:
                    om_existing.id = snapshot_map_id
                else:
                    world.add(eid, OnMap(id=snapshot_map_id))

                # if this is the local player and their map changed, activate that map
                if peer_id == my_peer_id and snapshot_map_id != prev_map_id:
                    target_id = resolve_map_hint_to_id(snapshot_map_id) or snapshot_map_id
                    create_or_activate(world, target_id)

                    # map transition SFX for local player
                    comps[SoundRequest] = SoundRequest(
                        event="map_transition",
                        global_event=True,
                    )

            # position from snapshot
            new_x = float(pdata.get("x", tr.x))
            new_y = float(pdata.get("y", tr.y))

            if peer_id == my_peer_id and isinstance(snapshot_map_id, str) and snapshot_map_id != prev_map_id:
                # On a map transition, snap to the new room
                tr.x = new_x
                tr.y = new_y
                tr.net_x = new_x
                tr.net_y = new_y
            else:
                # Normal smoothing 
                tr.net_x = new_x
                tr.net_y = new_y

            # life and facing
            life.hp = float(pdata.get("hp", life.hp))
            facing.direction = pdata.get("facing", facing.direction)

            # player hit / death SFX for the Local player
            if peer_id == my_peer_id:
                if old_hp > 0 and life.hp <= 0:
                    comps[SoundRequest] = SoundRequest(event="player_death")
                elif life.hp < old_hp:
                    comps[SoundRequest] = SoundRequest(event="player_hit")

            new_clip = pdata.get("clip", anim.clip)

            # if clip changes
            if new_clip != anim.clip:
                anim.clip = new_clip
                anim.time = 0.0
                anim.frame = 0
                anim.changed = True

            # found matching entity so stop scanning
            break

    # Enemies ###############################
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

        # record previous HP
        old_hp = life.hp

        tr.net_x = float(edata.get("x", tr.x))
        tr.net_y = float(edata.get("y", tr.y))
        facing.direction = edata.get("facing", facing.direction)

        anim.clip = edata.get("clip", anim.clip)
        anim.frame = int(edata.get("frame", anim.frame))
        anim.changed = True
        life.hp = float(edata.get("hp", life.hp))

        # sync OnMap from snapshot
        snapshot_map_id = edata.get("map_id")
        if isinstance(snapshot_map_id, str):
            om = comps.get(OnMap)
            if om is not None:
                om.id = snapshot_map_id
            else:
                comps[OnMap] = OnMap(id=snapshot_map_id)

        # enemy hit / death SFX on client
        size = _infer_enemy_size_from_atlas_id(atlas_id)
        if old_hp > 0 and life.hp <= 0:
            comps[SoundRequest] = SoundRequest(
                event="enemy_death",
                subtype=size,
            )
        elif life.hp < old_hp:
            comps[SoundRequest] = SoundRequest(
                event="enemy_hit",
                subtype=size,
            )

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

        # sync OnMap from snapshot
        snapshot_map_id = pdata.get("map_id")
        if isinstance(snapshot_map_id, str):
            om = comps.get(OnMap)
            if om is not None:
                om.id = snapshot_map_id
            else:
                comps[OnMap] = OnMap(id=snapshot_map_id)

    _cleanup_remote_category(world, "pickup", pickup_ids_in_snapshot)
