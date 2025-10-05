# ai for the entities
# game/world/systems/ai.py


#this is the code to summon the ai specifically chaser

        #Spawn chort enemy entity with components that it will use
        #self.chaser_1_id = create_enemy(self.world, kind="chort", pos=(100, 100), params={"target_id" : self.player_id})

import random
import time
from game.world.components import Transform, Intent, AI

#enemy ai system currently just chases. could and will probably check to see if it is the chase ai or another.

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

        # chase entities
        for entity_id, comps in world.query(Transform, Intent, AI): #possible later addition WonderAI
            ai: AI = comps[AI]
            pos: Transform = comps[Transform]
            intent: Intent = comps[Intent]

            
            target_pos: Transform = world.get(ai.target_id, Transform)
            if pos is None or target_pos is None:
                continue

               
            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5
            # only handle chase entities
            if ai.kind == "chase":
                if dist > 10 and dist < ai.agro_range:  
                    intent.move_x = dx / dist
                    intent.move_y = dy / dist
                else:
                    intent.move_x = 0.0
                    intent.move_y = 0.0

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
            