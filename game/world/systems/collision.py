#Class collision

import math
import pygame
from game.world.components import Transform, HitboxSize, PlayerTag
from game.core.config import Config

class CollisionSystem:
    def __init__(self, collision_rects=None):
        self.knockbacks = {}
        self.collision_rects = collision_rects or []

    def update(self, world, dt: float):
        # Apply knockback to any entity currently in knockback
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

        # Check collisions for all entities with Transform
        for eid, comps in world.query(Transform):
            tr = comps[Transform]

            # Get this entity's hitbox radius (default 10 if not defined)
            hitbox = world.get(eid, HitboxSize)
            entity_radius = hitbox.radius if hitbox else 10

            # Player vs enemy knockback
            if eid != self.player_id:
                player_tr = world.get(self.player_id, Transform)
                if player_tr:
                    player_hitbox = world.get(self.player_id, HitboxSize)
                    player_radius = player_hitbox.radius if player_hitbox else 10

                    dx = player_tr.x - tr.x
                    dy = player_tr.y - tr.y
                    distance = math.sqrt(dx*dx + dy*dy)

                    # Use sum of radii for circle overlap check
                    if distance < (player_radius + entity_radius) and distance > 0:
                        dx /= distance
                        dy /= distance
                        self.knockbacks[self.player_id] = {"timer": 0.2, "dir": (dx, dy)}
                        self.knockbacks[eid] = {"timer": 0.2, "dir": (-dx, -dy)}
        
        # get list of player entities
        players = []
        for player_entity, _ in world.query(PlayerTag):
            players.append(player_entity)

        # Check collisions for all entities
        for eid, comps in world.query(Transform):
            tr = comps[Transform]

            # for each player
            for player_entity in players:
                # Players vs enemies knockback
                if eid not in players:
                    player_tr = world.get(player_entity, Transform)
                    if player_tr:
                        dx = player_tr.x - tr.x
                        dy = player_tr.y - tr.y
                        distance = math.sqrt(dx*dx + dy*dy)
                        if distance < 10 and distance > 0:
                            dx /= distance
                            dy /= distance
                            self.knockbacks[player_entity] = {"timer": 0.2, "dir": (dx, dy)}
                            self.knockbacks[eid] = {"timer": 0.2, "dir": (-dx, -dy)}

            # Wall collisions (using a simple 16x16 rect, could be adjusted)
            entity_rect = pygame.Rect(tr.x, tr.y, entity_radius * 2, entity_radius * 2)
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
