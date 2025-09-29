#Class collision
from game.world.components import Transform
import pygame
import math
from game.core.config import Config

class CollisionSystem:
    def __init__(self, player_id: int, collision_rects=None):
        self.player_id = player_id
        self.knockbacks = {}
        self.collision_rects = collision_rects or []

    def update(self, world, dt: float):
        # Apply knockback to any entity currently in knockback... the player and the enemy that collieded
        expired = []
        for eid, state in self.knockbacks.items():
            if state["timer"] > 0:
                state["timer"] -= dt
                tr = world.get(eid, Transform)
                # ease-out effect
                if tr:
                    strength = Config.KNOCKBACK_STRENGTH * (state["timer"] / 0.2)
                    tr.x += state["dir"][0] * strength * dt
                    tr.y += state["dir"][1] * strength * dt
            else:
                expired.append(eid)

        # Clean up finished knockbacks
        for eid in expired:
            del self.knockbacks[eid]

        # Check collisions for all entities
        for eid, comps in world.query(Transform):
            tr = comps[Transform]

            # Player vs enemies knockback
            if eid != self.player_id:
                player_tr = world.get(self.player_id, Transform)
                if player_tr:
                    dx = player_tr.x - tr.x
                    dy = player_tr.y - tr.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance < 10 and distance > 0:
                        dx /= distance
                        dy /= distance
                        self.knockbacks[self.player_id] = {"timer": 0.2, "dir": (dx, dy)}
                        self.knockbacks[eid] = {"timer": 0.2, "dir": (-dx, -dy)}

            # Wall collisions
            entity_rect = pygame.Rect(tr.x, tr.y, 16, 16)  # adjust to entity size
            for rect in self.collision_rects:
                if entity_rect.colliderect(rect):
                    # Calculate minimum push distance
                    dx_left = rect.right - entity_rect.left
                    dx_right = rect.left - entity_rect.right
                    dy_top = rect.bottom - entity_rect.top
                    dy_bottom = rect.top - entity_rect.bottom

                    # Push along the smaller overlap
                    overlaps = {
                        "left": abs(dx_left),
                        "right": abs(dx_right),
                        "top": abs(dy_top),
                        "bottom": abs(dy_bottom)
                    }
                    min_dir = min(overlaps, key=overlaps.get)
                    if min_dir == "left":
                        tr.x += dx_left
                    elif min_dir == "right":
                        tr.x += dx_right
                    elif min_dir == "top":
                        tr.y += dy_top
                    elif min_dir == "bottom":
                        tr.y += dy_bottom