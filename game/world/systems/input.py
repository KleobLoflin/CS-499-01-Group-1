# Class input

# client-side input system that reads mouse/keyboard and writes local players
# intent component.

# intent: what the player wants to do.

# DungeonScene uses this to build client-to-server_input packets and will
# end up using the local entity's intent component for client prediction.

# client prediction is necessary to cover up latency caused from having to
# wait for the server to validate everthing and send back snapshots

import pygame
from game.world.components import Intent

class InputSystem:
    
    def __init__(self, player_id: int) -> None:
        self.player_id = player_id # which entity to write intent to

    def update(self, world, dt: float) -> None:
        intent: Intent = world.get(self.player_id, Intent)
        if intent is None:  # incase player is not spawned yet
            return
        
        # get list of keys that are currently pressed
        keys = pygame.key.get_pressed()

        # convert wsad/arrow keys to axis (-1, 0, or 1)
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN])  - (keys[pygame.K_w] or keys[pygame.K_UP])

        # normalize diagonal speed, otherwise diagonal movement will be faster than cardinal
        if dx and dy:
            inv = 0.70710678118  # 1/sqrt(2)
            dx *= inv; dy *= inv

        # write intent values
        intent.move_x = float(dx)
        intent.move_y = float(dy)
