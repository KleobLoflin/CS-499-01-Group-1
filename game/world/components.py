from dataclasses import dataclass
from typing import Tuple

# ---- gameplay data ----
@dataclass
class Transform:
    x: float
    y: float

@dataclass
class Intent:
    move_x: float = 0.0   # -1..1
    move_y: float = 0.0

# ---- presentation ----
@dataclass
class DebugRect:
    size: Tuple[int, int] = (32, 32)
    color: Tuple[int, int, int] = (90, 180, 255)
