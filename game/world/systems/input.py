# Class input

# client-side input system that reads mouse/keyboard and writes local players
# intent component.

# intent: what the player wants to do.

# DungeonScene uses this to build client-to-server_input packets and will
# end up using the local entity's intent component for client prediction.

# client prediction is necessary to cover up latency caused from having to
# wait for the server to validate everthing and send back snapshots

import pygame
from game.world.components import Intent, InputState

KEY_TO_DIRECTION = {
    pygame.K_w: "up",
    pygame.K_s: "down",     
    pygame.K_a: "left",     
    pygame.K_d: "right",    
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right"
}

ATTACK_KEYS = {pygame.K_SPACE}
DASH_KEYS = {pygame.K_LSHIFT, pygame.K_RSHIFT}

class InputSystem:
    def __init__(self, player_id: int) -> None:
        self.player_id = player_id
    
    def update(self, world, dt: float):
        comps = world.entities.get(self.player_id)
        input: InputState = comps.get(InputState)
        intent: Intent = comps.get(Intent)

        # get key presses and write input state
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        
        # get key order ##########################################################
        now_pressed = set()
        for key, direction in KEY_TO_DIRECTION.items():
            if keys[key]:
                now_pressed.add(direction)

        for direction in ("up", "down", "left", "right"):
            if direction not in now_pressed and direction in input.key_order:
                input.key_order.remove(direction)
            elif direction in now_pressed and direction not in input.key_order:
                input.key_order.append(direction)
        
        # actions ############################################################
        for key in ATTACK_KEYS:
            if keys[key]:
                intent.basic_atk = True
                break
                
        for key in DASH_KEYS:
            if keys[key]:
                intent.dash = True
                break
            else:
                intent.dash = False

        # movement ##########################################################
        dx = int("right" in now_pressed) - int("left" in now_pressed)
        dy = int("down" in now_pressed) - int("up" in now_pressed)
        intent.move_x = float(dx)
        intent.move_y = float(dy)

        # facing
        if now_pressed:
            for direction in input.key_order:
                if direction in now_pressed:
                    intent.facing = direction
                    break
        