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
from game.core.config import Config

class InputSystem:

    def __init__(self, player_id: int) -> None:
        self.player_id = player_id
        pygame.key.set_repeat(0)

        # Dash state
        self.dash_x = 0.0
        self.dash_y = 0.0
        self.dash_cooldown = 0.0  # cooldown timer

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                if self.dash_cooldown <= 0.0:  # only allow if cooldown expired
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                        self.dash_x = 1.0
                    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                        self.dash_x = -1.0
                    if keys[pygame.K_w] or keys[pygame.K_UP]:
                        self.dash_y = -1.0
                    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                        self.dash_y = 1.0
                    
                    # Start cooldown
                    if self.dash_x or self.dash_y:
                        self.dash_cooldown = Config.DASH_TIMER

    def update(self, world, dt: float) -> None:
        intent: Intent = world.get(self.player_id, Intent)
        if intent is None:
            return

        # Decrement cooldown
        if self.dash_cooldown > 0.0:
            self.dash_cooldown -= dt

        # Movement input
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN])  - (keys[pygame.K_w] or keys[pygame.K_UP])

        if dx and dy:
            inv = 0.70710678118
            dx *= inv; dy *= inv

        intent.move_x = float(dx)
        intent.move_y = float(dy)

        # Pass dash intent (one-frame trigger)
        intent.dash_x = self.dash_x
        intent.dash_y = self.dash_y

        # Reset after use
        self.dash_x = 0.0
        self.dash_y = 0.0
