#WORKED ON BY: Colin Adams, Scott Petty, Nicholas Loflin, Matthew Payne, Cole Herzog
#Class collision
from game.world.components import Transform, HitboxSize, PlayerTag, Map, ActiveMapId, OnMap,  Projectile, Life, SoundRequest, AI
import pygame
import math
from game.core.config import Config

class CollisionSystem:
    def __init__(self, collision_rects=None):
        self.knockbacks = {}
        self.damage_cooldowns = {} # per-player damage cooldowns
        self.collision_rects = collision_rects or []

    def update(self, world, dt: float):
        # Update damage cooldowns
        for pid in list(self.damage_cooldowns.keys()):
            self.damage_cooldowns[pid] -= dt
            if self.damage_cooldowns[pid] <= 0:
                del self.damage_cooldowns[pid]

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
        
        # build player -> map info
        players: list[int] = []
        player_map: dict[int, str] = {}
        player_maps: set[str] = set()

        for pid, comps in world.query(PlayerTag, OnMap):
            om: OnMap = comps[OnMap]
            players.append(pid)
            player_map[pid] = om.id
            player_maps.add(om.id)
        
        # if no players
        if not players:
            return
        
        # get collision rects per map
        collisions_by_map: dict[str, list[pygame.Rect]] = {}
        for _, comps in world.query(Map):
            m: Map = comps[Map]
            if not m.collisions:
                continue
            
            # only keep maps that currently have players on them
            if player_maps and m.id not in player_maps:
                continue
            collisions_by_map[m.id] = m.collisions

        # incase still need self.collision_rects
        global_collisions = self.collision_rects or []

        # if no per-map collisions or global collisions
        if not collisions_by_map and not global_collisions:
            return
        
        # check collisions for all entities
        for eid, comps in world.query(Transform):
            tr = comps[Transform]

            # determine which map entity is on
            ent_on = comps.get(OnMap)
            ent_map_id = ent_on.id if ent_on is not None else None

            # if entity has OnMap and that map has no players then skip
            if ent_map_id is not None and ent_map_id not in player_maps:
                continue

            # get entity's hitbox radius
            hitbox = world.get(eid, HitboxSize)
            entity_radius = hitbox.radius if hitbox else 10

            # for each player on the same map
            for player_entity in players:
                if ent_map_id is not None:
                    if player_map.get(player_entity) != ent_map_id:
                        continue

                # Players vs enemies knockback
                if eid not in players:
                    player_tr = world.get(player_entity, Transform)
                    if player_tr:
                        player_hitbox = world.get(player_entity, HitboxSize)
                        player_radius = player_hitbox.radius if player_hitbox else 10

                        dx = player_tr.x - tr.x
                        dy = player_tr.y - tr.y
                        distance = math.sqrt(dx*dx + dy*dy)
                        if 0 < distance < 10:
                            dx /= distance
                            dy /= distance

                            # Is this thing allowed to hurt the player?
                            is_enemy = world.get(eid, AI) is not None
                            is_projectile = world.get(eid, Projectile) is not None

                            # Only deal damage when starting a new knockback so we
                            # don't drain HP every frame while overlapping.
                            if player_entity not in self.damage_cooldowns and (is_enemy or is_projectile):
                                life = world.get(player_entity, Life)
                                if life:
                                    life.hp -= 1  # -1 HP per enemy / projectile hit

                                    # Trigger player-hit sound on the player
                                    pcomps = world.components_of(player_entity)
                                    pcomps[SoundRequest] = SoundRequest(event="player_hit")

                                    # Set damage cooldown (tune this value as needed)
                                    self.damage_cooldowns[player_entity] = 0.5  # 0.5s of invuln

                            # Knockback to player (same as before)
                            self.knockbacks[player_entity] = {"timer": 0.2, "dir": (dx, dy)}
                            # Knockback to the other entity (same as before)
                            self.knockbacks[eid] = {"timer": 0.2, "dir": (-dx, -dy)}

                            # If this is a projectile, consume it on hit so it
                            # doesn't keep colliding and dealing damage.
                            if is_projectile:
                                world.delete_entity(eid)
                                break

            
            entity_radius = (hitbox.radius / 2) if hitbox else 5

            # pick per-map collision rects for this entity
            if ent_map_id is not None:
                collisions = collisions_by_map.get(ent_map_id, [])
            else:
                collisions = global_collisions

            # wall collisions
            entity_rect = pygame.Rect(
                tr.x - entity_radius,
                tr.y - entity_radius,
                entity_radius * 2,
                entity_radius - 2 # -2 is required for bottom wall collision aestetics
            )
            for rect in collisions:
                if entity_rect.colliderect(rect):

                    if world.get(eid, Projectile):
                        world.delete_entity(eid)
                        break
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
