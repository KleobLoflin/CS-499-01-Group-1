# ai for the entities
# game/world/systems/ai.py


#this is the code to summon the ai specifically chaser

        #Spawn chort enemy entity with components that it will use
        #self.chaser_1_id = create_enemy(self.world, kind="chort", pos=(100, 100), params={"target_id" : self.player_id})

import random
import time
from game.world.components import Transform, Intent, AI, PlayerTag, OnMap, ActiveMapId

# Moved AI dataclasses to components and now there is a "kind" label for the different kinds of AI.
# I filtered each code block for ai.kind so that it only runs if the kind of AI matches.
# you can add code blocks for as many AI kinds as you want and just filter for the ai.kind string of choice.
# I also removed the target.id check for wonder ai because it doesnt target a player
# -Scott


#find away to make that an ai switches between the 3 states as needed. 
#need an agro range.
#need a place for them to stop if to close or to far agro range again i guess.
#need another way to make a porjectile attack.

class EnemyAISystem:#System):
    
    def update(self, world, dt: float) -> None:
        
        # get active map ID
        active_id = None
        for _, comps in world.query(ActiveMapId):
             active_id = comps[ActiveMapId].id
             break
        
        # pick a player on this map
        # just picks the first player in the entity list for now
        # later, get a list of players that are on the map and then use the list
        # to find the right target_id for each of the enemy ai types depending on distance
        player_tr = None
        for _, comps in world.query(Transform, PlayerTag):
            if active_id is not None:
                om = comps.get(OnMap)
                if om is None or om.id != active_id:
                    continue
            player_tr = comps[Transform]
            break
        if player_tr is None:
            return


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
            if ai.kind in ("chase", "flee"):
                # prefer AI.target_id if provided, else use first player on this map
                if getattr(ai, "target_id", None) is not None:
                    target_pos = world.get(ai.target_id, Transform)
                if target_pos is None:
                    target_pos = player_tr
                if target_pos is None:
                    # no valid target
                    intent.move_x = 0.0
                    intent.move_y = 0.0
                    continue
               
            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5

            if dist > ai.agro_range:
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

                    # keep moving in that direction
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

                elif ai.kind == "wander":
                    dx = random.randint(-10, 10)
                    dy = random.randint(-10, 10)
                
                    if dist < 200 and dist > 0:
                        intent.move_x = -dx / dist
                        intent.move_y = -dy / dist
                    else:
                        intent.move_x = 0.0
                        intent.move_y = 0.0
            #elif ai.kind == "straight_line":
            #    intent.move_x = dx / dist
            #    intent.move_y = dy / dist

                #BELOW THIS needs to be worked on
            #elif ai.kind == "ranged" and target_pos:
            #    ai.max_cooldown -= dt
            #    if 10 < dist < ai.agro_range and ai.max_cooldown <= 0:
            #        ai.max_cooldown = ai.max_cooldown  # reset attack cooldown

        # spawn projectile
            #proj_id = world.new_entity()
            #bp = enemy_bp("projectile.arrow")  # blueprint for arrow
            #ctx = {"pos": (pos.x, pos.y), "owner": entity_id, "target_id": ai.target_id}
            #apply_blueprint(world, proj_id, bp, ctx)

        # optional: face target
            #intent.facing = "left" if dx < 0 else "right

            # facing
            if intent.move_x < -0.01:
                    intent.facing = "left"
            elif intent.move_x > 0.01:
                    intent.facing = "right"



           #ADD A PROJECTILE
           # CODE TO FIND DISTANCE AND GO IN STRAIGHT ORDER.
           # if range
           #delete after timer


           # ADD A TRAP 
            