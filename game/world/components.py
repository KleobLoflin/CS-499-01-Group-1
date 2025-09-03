# Components are data-only
# they become attached to entities when entities are created
# systems operate on the components data to make stuff happen

# @dataclass decorator with the custom data classes is just a python-style
# implementation of something like a struct from C,C++. It isnt the same thing
# memory-wise but it behaves similarly.

# 

from dataclasses import dataclass
from typing import Tuple

# gameplay data ##################################################

# transform: data representing world-space position
# later will add velocity, rotation, etc... anything needed for size/location/orientation
@dataclass
class Transform:
    x: float
    y: float

# intent: data representing what the player/enemy is trying to do
# this describes a per-tick input intent that is either written by 
# InputSystem (from client) or by the server. movement is [-1,1] on each axis
@dataclass
class Intent:
    move_x: float = 0.0   # -1..1
    move_y: float = 0.0

# presentation #####################################################

# this is just here to describe the rectangle we can move around
# later this will be Sprite + AnimationState used to draw a sprite frame
@dataclass
class DebugRect:
    size: Tuple[int, int] = (32, 32)
    color: Tuple[int, int, int] = (90, 180, 255)
