# Class input

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
        self.prev_attack_pressed = False  # edge detection
        self.prev_dash_pressed = False    # edge detection

    def update(self, world, dt: float):
        comps = world.entities.get(self.player_id)
        input: InputState = comps.get(InputState)
        intent: Intent = comps.get(Intent)

        # process events and key state
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        # ---------------- Movement directions ----------------
        now_pressed = set()
        for key, direction in KEY_TO_DIRECTION.items():
            if keys[key]:
                now_pressed.add(direction)

        # update key order for facing priority
        for direction in ("up", "down", "left", "right"):
            if direction not in now_pressed and direction in input.key_order:
                input.key_order.remove(direction)
            elif direction in now_pressed and direction not in input.key_order:
                input.key_order.append(direction)

        # ---------------- Actions ----------------
        # Attack (edge detection)
        attack_pressed = any(keys[k] for k in ATTACK_KEYS)
        if attack_pressed and not self.prev_attack_pressed:
            intent.basic_atk = True
        self.prev_attack_pressed = attack_pressed

        # Dash (edge detection)
        dash_pressed = any(keys[k] for k in DASH_KEYS)
        intent.dash = dash_pressed  # allow holding dash
        self.prev_dash_pressed = dash_pressed

        # ---------------- Movement axes ----------------
        dx = int("right" in now_pressed) - int("left" in now_pressed)
        dy = int("down" in now_pressed) - int("up" in now_pressed)
        intent.move_x = float(dx)
        intent.move_y = float(dy)

        # ---------------- Facing ----------------
        if now_pressed:
            for direction in input.key_order:
                if direction in now_pressed:
                    intent.facing = direction
                    break
