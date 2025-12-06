# AUTHORED BY: Scott Petty, Cole Herzog
# game/net/context.py
#
# Global networking context shared across scenes.
# This is where the NetServer / NetClient live so that when you swap scenes,
# the sockets are not destroyed. Scenes just "attach" these into their World as
# NetHostState / NetClientState components.

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, Literal

from game.net.server import NetServer
from game.net.client import NetClient

Role = Literal["SOLO", "HOST", "CLIENT"]
Address = Tuple[str, int]


@dataclass
class NetworkContext:
    role: Role = "SOLO"
    my_peer_id: str = "solo"

    # Sockets that must survive scene changes
    server: Optional[NetServer] = None   # only used in HOST role
    client: Optional[NetClient] = None   # only used in CLIENT role

    # Host-only: peer_id -> (ip, port)
    peers: Dict[str, Address] = field(default_factory=dict)

    # Optional hub/dungeon data (map + hero choices, etc.)
    lobby_data: dict = field(default_factory=dict)


# Single global instance imported everywhere
net = NetworkContext()
