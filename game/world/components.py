# AUTHORED BY: Scott Petty
# EDITED BY: ALL
# Components are data-only
# they become attached to entities when entities are created
# systems operate on the components data to make stuff happen

# @dataclass decorator with the custom data classes is just a python-style
# implementation of something like a struct from C,C++. It isnt the same thing
# memory-wise but it behaves similarly.

from dataclasses import dataclass, field
from typing import Tuple, Dict, Set, Literal, List, Optional, Any

# gameplay tags ##################################################

# to mark an entity as a player
@dataclass
class PlayerTag:  
    pass

# for local only control
@dataclass
class LocalControlled:
    pass

# transform: data representing world-space position
# later will add velocity, rotation, etc... anything needed for size/location/orientation
@dataclass
class Transform:
    x: float
    y: float

    # latest position from a host snapshot
    # for client interpolation
    net_x: Optional[float] = None
    net_y: Optional[float] = None

# any data constants that are involved in entity movement calculations
@dataclass
class Movement:
    speed: int
    dash_speed: int = 300
    dash_duration: float = 0.0
    dash_cooldown: float = 0.0
    dash_max_cooldown: float = 1.0
    dash_max_duration: float = 0.175
 
# intent: data representing what the player/enemy is trying to do
# this describes a per-tick input intent that is either written by 
# InputSystem (from client) or by the server. movement is [-1,1] on each axis
@dataclass
class Intent:
    move_x: float = 0.0   # -1..1
    move_y: float = 0.0   # -1..1
    basic_atk: bool = False
    basic_atk_held: bool = False
    dash: bool = False
    special_atk: bool = False
    facing: Literal["up", "down", "left", "right"] = "down"

@dataclass
class InputState:
    key_order: List[str] = field(default_factory=list)
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    accept: bool = False
    back: bool = False
    prev_attack_pressed: bool = False
    prev_dash_pressed: bool = False

@dataclass
class Attack:
    max_cooldown: float = 0.15
    remaining_cooldown: float = max_cooldown
    active: bool = False
    damage: float = 1

# Hitbox Size
@dataclass
class HitboxSize:
    radius: float = 10.0   # default hitbox size, can be overridden in JSON


# Enemy AI Patterns
@dataclass
class AI:
    kind: str   # current kinds: "chase", "flee", "wander", ...
    target_id: int|None = None  # explicit target; None = auto-pick nearest player
    agro_range: int = 0   # distance to start chasing
    aggro_sfx_played: bool = False
    aggro_sfx_played: bool = False


@dataclass
class lifeSpan:
    duration: float = 5.0    # seconds until entity is removed
    elapsed: float = 0.0     # time elapsed since creation



@dataclass
class Life:
    hp: float = 5.0    # hp it currently has

@dataclass
class Damage:
    amount: float = 1.0   # damage to apply
    owner_id: Optional[int] = None  # entity that caused the damage
    # friendly fire option here later?
    


# presentation #####################################################

@dataclass
class Sprite:
    atlas_id: str   # id's used for mapping sprites ("hero.knight", "enemy.chort")
    z: int = 10     # draw order (bigger number draws last)

@dataclass
class AnimationState:
    clip: str = "idle"  # current clip name
    frame: int = 0
    time: float = 0.0
    fps: float = 0.0    # 0 means use the atlas default for this clip
    loop: bool = True
    changed: bool = True    # set true when clip changes so we can reset time

@dataclass
class Facing:
    direction: Literal["up", "down", "left", "right"] = "right"

@dataclass
class DebugRect:
    size: Tuple[int, int] = (32, 32)
    color: Tuple[int, int, int] = (90, 180, 255)

# Map and Spawn ##############################################################

# map data
@dataclass
class Map:
    name: str                # file name
    path: str                # file path to .tmx
    tmx_data: any = None     # loaded pytmx map
    active: bool = False     # is this the current map

    id: Optional[str] = None                # registry id, ex: "level0"
    collisions: Optional[List[Any]] = None  # list[pygame.rect] or (x, y, w, h)
    music: Optional[str] = None
    ambience: Optional[str] = None
    blueprint: Optional[Dict[str, Any]] = None  # parsed <map>.blueprint.json

# client-side which map to render/simulate
@dataclass
class ActiveMapId:
    id: str         

# attach to any entity that belongs to a specific Map.id
@dataclass
class OnMap:
    id: str         

# lives on the Map entity, ensures spawns happen once per map
@dataclass
class MapSpawnState:
    did_initial_spawns: bool = False
    did_title_spawns: bool = False

# run/scene-level policy used by SpawnSystem
@dataclass
class SpawnPolicy:      
    spawn_player: bool = False
    spawn_static_enemies: bool = True
    spawn_pickups: bool = True
    spawn_objects: bool = True

    run_title_spawns: bool = False
    run_game_spawns: bool = True

# pickups/objects placeholders ##############

@dataclass
class Pickup:
    kind: str = "potion_health"     # powerups, potions, weapons, keys, coins, etc...

@dataclass
class WorldObject:
    kind: str = "chest"         # chests, fountains, columns, barriers, spikes, doors, etc...

# Title Menu ############################################

@dataclass
class TitleMenu:
    title: str = "GateCrashers"
    options: List[str] = field(default_factory=lambda: ["single_player", "host", "join", "settings", "quit"])
    selected_index: int = 0
    selected_role: Optional[str] = None

@dataclass
class TitleIntro:
    phase: str = "pre_delay"    # pre_delay -> logo_fade -> hold -> bg_fade -> ready
    t: float = 0.0              # elapsed time in current phase
    logo_alpha: int = 0         # 0...255
    bg_alpha: int = 0           # 0...255

    # tunable constants
    pre_delay_dur: float = 0.75
    logo_fade_dur: float = 2.5
    logo_hold_dur: float = 1.25
    bg_fade_dur: float = 2.0

# Camera ##################################################
@dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0
    viewport_w: int = 640
    viewport_h: int = 360
    deadzone_w: int = 96
    deadzone_h: int = 64
    clamp_rect: Optional[Tuple[int, int, int ,int]] = None
    pixel_snap: bool = True

@dataclass
class CameraFollowLocalPlayer:
    pass

# Networking id and ownership ##################################

@dataclass
class NetIdentity:
    my_peer_id: str     # "host", "solo", "peer:abcd"
    role: str           # "HOST" | "CLIENT" | "SOLO"

@dataclass
class Owner:
    peer_id: str        # who owns/controls this entity

# Hub / Lobby ##################################################

@dataclass
class LobbySlot:
    # one slot per player. up to five.
    index: int
    player_eid: Optional[int] = None    # eid of PlayerTag when occupied
    is_local: bool = False              
    selected_char_index: int = 0        # which hero in the catalog
    ready: bool = False
    name: str = "Player"
    preview_eid: Optional[int] = None   # entity that displays idle animation
    peer_id: Optional[str] = None       # owner id for this slot

@dataclass
class LobbyState:
    mode: str = "SINGLE"        # "SINGLE" | "HOST" | "JOIN"
    substate: str = "SELECT"    # "BROWSER" for Join server list, else "SELECT"
    character_catalog: List[str] = field(default_factory=list)

@dataclass
class AvailableHosts:
    hosts: List[str] = field(default_factory=list)
    selected_index: int = 0

@dataclass
class SpawnRequest:     # use to pass player spawn info to DungeonScene
    hero_key: str       # example: "hero.knight_blue"
    is_local: bool      # if true, attach LocalControlled at gameplay
    player_name: str = "Player"
    net_id: Optional[str] = None    # use for networking

# Networking host/client state #####################################################

@dataclass
class NetHostState:
    server: Any = None                      # game.net.server.NetServer instance
    tick: int = 0                           # simulation/network tick
    accumulator: float = 0.0                # time accumulator for snapshot sends
    send_interval: float = 1.0 / 60.0       # send snapshots at ~60Hz by default
    max_clients: int = 4                    # up to 4 clients (5 total players w/ host)
    # peer_id -> (ip, port)
    peers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetClientState:
    client: Any = None                      # game.net.client.NetClient instance
    tick: int = 0                           # local input tick
    accumulator: float = 0.0                # time accumulator for input sends
    send_interval: float = 1.0 / 60.0       # send inputs at ~60Hz
    last_snapshot_tick: int = 0             # last snapshot we applied
    prediction: bool = True                 # hook for client-side prediction
    interpolation: bool = True              # hook for snapshot interpolation

# marks an entity as a client-side proxy for something that actually lives on the host
@dataclass
class RemoteEntity:
    remote_id: int
    category: str = "generic"

# scoring components

@dataclass
class Score:
    #Attach to a player entity. Holds the player's current score.
    points: int = 0

@dataclass
class Scored:
    #Marker added to a dead/consumed entity so we don't award score multiple times.
    reason: str = "" 
    
@dataclass
class ScoreValue:
    amount: int = 0

@dataclass
class LastHitBy:
    attacker_eid: int = -1

# Sound ##############################################################################################

@dataclass
class SoundRequest:
    event: str                          # "player_swing", "enemy_aggro", "enemy_hit", etc...
    subtype: Optional[str] = None       # enemy size/type
    global_event: bool = False          # for UI/map transitions