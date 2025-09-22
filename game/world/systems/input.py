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
        input_state: InputState = comps.get(InputState)
        intent: Intent = comps.get(Intent)

        # get key presses and write input state
        keys = pygame.key.get_pressed()
        
        # directions ##########################################################
        for key in keys:
            if key in KEY_TO_DIRECTION:
                input_state.directions_held.add(KEY_TO_DIRECTION[key])
        
        # add directions to order list
        for direction in ("up", "down", "left", "right"):
            if direction in input_state.directions_held:
                input_state.directions_order.append(direction)
        
        # remove no longer held directions from the order list
        for direction in list(input_state.directions_order):
            if direction not in input_state.directions_held:
                input_state.directions_order.remove(direction)
        
        # actions ############################################################
        for key in keys:
            if key in ATTACK_KEYS:
                input_state.action["basic_attack"] = True
            else:
                input_state.action["basic_attack"] = False
            if key in DASH_KEYS:
                input_state.action["dash"] = True
            else:
                input_state.action["dash"] = False

        # write to intent component
        # movement
        dx = int("right" in input_state.directions_held) - int("left" in input_state.directions_held)
        dy = int("down" in input_state.directions_held) - int("up" in input_state.directions_held)
        intent.move_x = float(dx)
        intent.move_y = float(dy)

        # facing
        if input_state.directions_held:
            for direction in input_state.directions_order:
                if direction in input_state.directions_held:
                    intent.facing = direction
                    break
        
        # attack
        intent.basic_atk = input_state.action["basic_attack"]
        
        # dash
        intent.dash = input_state.action["dash"]