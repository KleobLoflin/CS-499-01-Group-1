# Class collision
from game.world.components import Transform
import math
from game.core.config import Config

class CollisionSystem:
    def __init__(self, player_id: int) -> None:
        self.player_id = player_id
        self.knockbacks = {}

    def update(self, world, dt: float) -> None:

        # Apply knockback to any entity currently in knockback... the player and the enemy that collieded
        expired = []
        for eid, state in self.knockbacks.items():
            if state["timer"] > 0:
                state["timer"] -= dt
                tr = world.get(eid, Transform)
                if tr:
                    # ease-out effect
                    strength = Config.KNOCKBACK_STRENGTH * (state["timer"] / 0.2)  
                    tr.x += state["dir"][0] * strength * dt
                    tr.y += state["dir"][1] * strength * dt
            else:
                expired.append(eid)

        # Clean up finished knockbacks
        for eid in expired:
            del self.knockbacks[eid]

        # Get player position
        player_pos = world.get(self.player_id, Transform)
        if not player_pos:
            return

        # Check collisions
        for eid, components in world.query(Transform):
            if eid == self.player_id:
                continue

            enemy_pos = components[Transform]

            dx = player_pos.x - enemy_pos.x
            dy = player_pos.y - enemy_pos.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 10:  # collision threshold adjust for how close the enemy must be for collision
                if distance > 0:
                    dx /= distance
                    dy /= distance

                    # Knockback player (away from enemy)
                    self.knockbacks[self.player_id] = {
                        "timer": 0.2,
                        "dir": (dx, dy),
                    }

                    # Knockback enemy (away from player)
                    self.knockbacks[eid] = {
                        "timer": 0.2,
                        "dir": (-dx, -dy),
                    }
