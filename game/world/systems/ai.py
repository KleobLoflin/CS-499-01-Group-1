# ai for the entities
# game/world/systems/ai.py


#this is the code to summon the ai specifically chaser
""" 
    #Spawn chase enemy entity with components that it will use
        self.chaser_id = self.world.new_entity()
        self.world.add(self.chaser_id, Transform(x=100, y=100))  # enemy starts in corner
        self.world.add(self.chaser_id, Intent())
        self.world.add(self.chaser_id, DebugRect(size=Config.RECT_SIZE, color=(255, 0, 0)))  # red enemy
        self.world.add(self.chaser_id,  ChaseAI(target_id=self.player_id))       # a system with update(world, dt)
 """
import random
import time
from game.world.components import Transform, Intent, AI

#enemy ai system currently just chases. could and will probably check to see if it is the chase ai or another.

# Moved AI dataclasses to components and now there is a "kind" label for the different kinds of AI.
# I filtered each code block for ai.kind so that it only runs if the kind of AI matches.
# you can add code blocks for as many AI kinds as you want and just filter for the ai.kind string of choice.
# I also removed the target.id check for wonder ai because it doesnt target a player
# -Scott
class EnemyAISystem:#System):
    
    def update(self, world, dt: float) -> None:

        # chase entities
        for entity_id, comps in world.query(Transform, Intent, AI): #possible later addition WonderAI
            ai: AI = comps[AI]

            # only handle chase entities
            if ai.kind != "chase":
                continue

            pos: Transform = comps[Transform]
            intent: Intent = comps[Intent]
            


            target_pos: Transform = world.get(ai.target_id, Transform)
            if pos is None or target_pos is None:
                continue

            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5

            target_pos: Transform = world.get(ai.target_id, Transform)
                
            if pos is None or target_pos is None:
                continue
                
            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5

            if dist > 0 and dist > 10:  # avoid division by zero and jitter
                intent.move_x = dx / dist
                intent.move_y = dy / dist
            else:
                intent.move_x = 0.0
                intent.move_y = 0.0



        # flee entities
        for entity_id, comps in world.query(Transform, Intent, AI):
            ai: AI = comps[AI]
            
            # only handle flee entities
            if ai.kind != "flee":
                continue

            pos: Transform = comps[Transform]
            intent: Intent = comps[Intent]
            
            
            target_pos: Transform = world.get(ai.target_id, Transform)
            if pos is None or target_pos is None:
                continue

            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5

            if dist < 200 and dist > 0:
                intent.move_x = -dx / dist
                intent.move_y = -dy / dist
            else:
                intent.move_x = 0.0
                intent.move_y = 0.0



        # wonder entities this crashes everything
        for entity_id, comps in world.query(Transform, Intent, AI):
            ai: AI = comps[AI]

            # only handle wonder entities
            if ai.kind != "wander":
                continue
            
            pos: Transform = comps[Transform]
            intent: Intent = comps[Intent]

            #time.sleep(4 )  crashes the shit out of everything  
            dx = random.randint(-10, 10)
            dy = random.randint(-10, 10)            
            
            dist = (dx * dx + dy * dy) ** 0.5

            if dist < 200 and dist > 0:
                intent.move_x = -dx / dist
                intent.move_y = -dy / dist
            else:
                intent.move_x = 0.0
                intent.move_y = 0.0