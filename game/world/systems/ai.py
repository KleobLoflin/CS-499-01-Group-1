# ai for the entities
# game/world/systems/ai.py


#this is the code to summon the ai specifically chaser

        #Spawn chort enemy entity with components that it will use
        #self.chaser_1_id = create_enemy(self.world, kind="chort", pos=(100, 100), params={"target_id" : self.player_id})

import random
import time
from game.world.actors.enemy_factory import create as create_enemy
from game.world.components import Transform, Intent, AI, PlayerTag, OnMap, ActiveMapId, Attack
from game.world.actors.blueprint import apply_blueprint
from game.world.actors.blueprint_index import enemy as enemy_bp
# Moved AI dataclasses to components and now there is a "kind" label for the different kinds of AI.
# I filtered each code block for ai.kind so that it only runs if the kind of AI matches.
# you can add code blocks for as many AI kinds as you want and just filter for the ai.kind string of choice.
# I also removed the target.id check for wonder ai because it doesnt target a player
# -Scott


class EnemyAISystem:#System):
    
    def update(self, world, dt: float) -> None:
        
        # get active map ID
        active_id = None
        for _, comps in world.query(ActiveMapId):
             active_id = comps[ActiveMapId].id
             break
        
        # get all players on the map
        player_tr: list[Transform] = []
        for _, comps in world.query(Transform, PlayerTag):
            if active_id is not None:
                om = comps.get(OnMap)
                if om is None or om.id != active_id:
                    continue
            player_tr.append(comps[Transform])

        # drive AI for entities with AI + Transform + Intent
        for entity_id, comps in world.query(Transform, Intent, AI): 
            # only move entities that are on the map
            if active_id is not None:
                om = comps.get(OnMap)
                if om is None or om.id != active_id:
                    continue

            ai: AI = comps[AI]
            pos: Transform = comps[Transform]
            intent: Intent = comps[Intent]

            # choose target position
            target_pos: Transform | None = None
            
            # prefer AI.target_id if provided
            if getattr(ai, "target_id", None) is not None:
                target_pos = world.get(ai.target_id, Transform)

            # otherwise, pick nearest player on this map
            if target_pos is None and player_tr:
                best_tr: Transform | None = None
                best_dist2 = float("inf")
                for p_tr in player_tr:
                    dx = p_tr.x - pos.x
                    dy = p_tr.y - pos.y
                    d2 = dx * dx + dy * dy
                    if d2 < best_dist2:
                        best_dist2 = d2
                        best_tr = p_tr
                target_pos = best_tr
            
            # compute distance to target
            dx = 0.0
            dy = 0.0
            dist = float("inf")
            if target_pos != None:
                dx = target_pos.x - pos.x
                dy = target_pos.y - pos.y
                dist = (dx * dx + dy * dy) ** 0.5

            if dist > ai.agro_range or target_pos == None:
        # Give each AI its own cooldown + direction if not already present
                if not hasattr(ai, "wander_timer"):
                    ai.wander_timer = 0.0
                if not hasattr(ai, "wander_dir"):
                    ai.wander_dir = (0.0, 0.0)
                if not hasattr(ai, "wander_waiting"):
                    ai.wander_waiting = False

                ai.wander_timer -= dt
                if ai.wander_waiting:
                    if ai.wander_timer <= 0:

                        ai.wander_waiting = False
                        dx = random.randint(-10, 10)
                        dy = random.randint(-10, 10)
                        mag = max((dx * dx + dy * dy) ** 0.5, 1.0)
                        ai.wander_dir = (dx / mag, dy / mag)
                        ai.wander_timer = 1.0  # pick new direction every 1 second

                    # waiting
                    intent.move_x = 0.0
                    intent.move_y = 0.0
                else:
                    if ai.wander_timer <= 0:
                        ai.wander_waiting = True
                        ai.wander_timer = random.uniform(3.0,4.0)  # wait between 1-3 seconds
                        intent.move_x = 0.0
                        intent.move_y = 0.0
                    else:
                        # keep moving in that direction
                        intent.move_x = ai.wander_dir[0]
                        intent.move_y = ai.wander_dir[1]

            else:
                # only handle chase entities
                if ai.kind == "chase" or "projectileHoming":
                    if dist > 10 and dist < ai.agro_range:  
                        intent.move_x = dx / dist
                        intent.move_y = dy / dist
                    else:
                        intent.move_x = 0.0
                        intent.move_y = 0.0
                    #if ai.kind == "projectileHoming":

                elif ai.kind == "flee":
                
                    if dist < ai.agro_range and dist > 10:
                        intent.move_x = -dx / dist
                        intent.move_y = -dy / dist
                    else:
                        intent.move_x = 0.0
                        intent.move_y = 0.0

                #believed to work not sure tho
                elif ai.kind == "StraightLine":
                    if not hasattr(ai, "fixed_dir") and target_pos is not None:
                        # Calculate player direction at creation
                        dx0 = target_pos.x - pos.x
                        dy0 = target_pos.y - pos.y
                        d0 = max((dx0 * dx0 + dy0 * dy0) ** 0.5, 1.0)
                        ai.fixed_dir = (dx0 / d0, dy0 / d0)
                    
                    # Move along the fixed direction each frame
                    intent.move_x = ai.fixed_dir[0]
                    intent.move_y = ai.fixed_dir[1]

                elif ai.kind == "Ranged":
                    atk = comps.get(Attack)
                    if not atk or not target_pos:
                        return

                    if atk.remaining_cooldown > 0:
                        atk.remaining_cooldown -= dt

                    intent.move_x = 0.0
                    intent.move_y = 0.0

                    if dist < ai.agro_range and dist > 10:
                        if atk.remaining_cooldown <= 0:
                            atk.remaining_cooldown = atk.max_cooldown

                            self.spawn_projectile(
                                world=world,
                                pos=pos,
                                target_pos=target_pos,
                                owner_id=entity_id,
                                active_id=active_id,
                                target_id=getattr(ai, "target_id", None)
                            )



        # optional: face target
            #intent.facing = "left" if dx < 0 else "right

            # facing
            if intent.move_x < -0.01:
                    intent.facing = "left"
            elif intent.move_x > 0.01:
                    intent.facing = "right"


    def spawn_projectile(self, world, pos, target_pos, owner_id, active_id, target_id):
        proj_id = create_enemy(
            world,
            kind="projectile.homingarrow",
            pos=(pos.x, pos.y),
            params={
                "owner": owner_id,
                "target_id": target_id
            }
        )

        world.add(proj_id, OnMap(id=active_id))

        # give initial direction
        dx = target_pos.x - pos.x
        dy = target_pos.y - pos.y
        dist = max((dx*dx + dy*dy)**0.5, 0.001)

        proj_intent = world.get(proj_id, Intent)
        if proj_intent:
            proj_intent.move_x = dx / dist
            proj_intent.move_y = dy / dist

        print("Projectile spawned:", proj_id)
