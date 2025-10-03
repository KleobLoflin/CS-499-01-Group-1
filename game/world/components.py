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

# any data constants that are involved in entity movement calculations
@dataclass
class Movement:
    speed: int
    dash_speed: int = 250
    dash_duration: float = 0.0
    dash_cooldown: float = 0.0
    dash_max_cooldown: float = 1.0
    dash_max_duration: float = 0.125
 
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
    facing: str = Literal["up", "down", "left", "right"]

@dataclass
class InputState:
    key_order: List[str] = field(default_factory=list)

@dataclass
class Attack:
    max_cooldown: float = 0.15
    remaining_cooldown: float = max_cooldown
    active: bool = False

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
    direction: str = Literal["up", "down", "left", "right"]

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

# Menus ############################################

@dataclass
class TitleMenu:
    title: str = "GateCrashers"
    options: List[str] = field(default_factory=lambda: ["Single Player", "Host", "Join"])
    selected_index: int = 0
    selected_role: Optional[str] = None