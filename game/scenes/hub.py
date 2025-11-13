# Class: HubScene(Scene)

# lobby/inventory/chat before gameplay
# Establishes a server connection, lets the party ready-up, and then transitions
# to DungeonScene

from game.scenes.base import Scene
from game.world.components import (
    LobbyState, LobbyMode, LobbySlot, AvailableHosts,
    NetworkRole, ConnectionHandle, PlayerTag, LocalControlled,
    InputState
)

# # systems
# from game.world.systems.hub import
# from game.world.systems.hub import
# from game.world.systems.hub import
# from game.world.systems.hub import

class HubScene(Scene):
    def __init__(self, scene_manager, role):
        self.sm = scene_manager
        self.role = role
        