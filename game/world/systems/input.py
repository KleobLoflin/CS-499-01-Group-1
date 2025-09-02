# Class input

# Maps keyboard/mouse state to a normalized Intent for the local player
# (move vector, aim vector, buttons)

# intent meaning, what the player wants to do.
# DungeonScene uses this to build client-to-server_input packets and will
# end up using the local entity's intent component for client prediction.

# client prediction is necessary to cover up latency caused from having to
# wait for the server to validate everthing and send back snapshots

import pygame
from game.world.components import Intent

class InputSystem:
    
    def __init__(self, player_id: int) -> None:
        self.player_id = player_id

    def update(self, world, dt: float) -> None:
        it: Intent = world.get(self.player_id, Intent)
        if it is None:
            return
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN])  - (keys[pygame.K_w] or keys[pygame.K_UP])

        # normalize diagonal (keep speed constant)
        if dx and dy:
            inv = 0.70710678118  # 1/sqrt(2)
            dx *= inv; dy *= inv

        it.move_x = float(dx)
        it.move_y = float(dy)
