# Class: HubScene(Scene)

# lobby/inventory/chat before gameplay; connects a NetClient
# possible fields: net, UI widgets...
# Establishes a server connection, lets the party ready-up, and then transitions
# to DungeonScene

from game.scenes.base import Scene