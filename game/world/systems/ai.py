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

from game.world.components import Transform, Intent

#basic chase ai maybe later add for it to stop in front of the player to attack
class ChaseAI:
    def __init__(self, target_id: int) -> None:
        self.target_id = target_id


class FleeAI:      #possible enemy ais to add later
    def __init__(self, target_id: int) -> None:
        self.target_id = target_id        

class WonderAI:    #same here
    def __init__(self, target_id: int) -> None:
        self.target_id = target_id


#enemy ai system currently just chases. could and will probably check to see if it is the chase ai or another.
class EnemyAISystem:#System):
    def update(self, world, dt: float) -> None:
        for entity_id, comps in world.query(Transform, Intent, ChaseAI): #possible later addition WonderAI
            pos: Transform = comps[Transform]
            intent: Intent = comps[Intent]
            ai: ChaseAI = comps[ChaseAI]
            #ai: FleeAI = comps[FleeAI]

            target_pos: Transform = world.get(ai.target_id, Transform)
            if pos is None or target_pos is None:
                continue

            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5


            if ChaseAI in comps:
                #ai: ChaseAI = comps[ChaseAI] 
                ai: ChaseAI = comps[ChaseAI]
                target_pos: Transform = world.get(ai.target_id, Transform)
                
                if pos is None or target_pos is None:
                    continue
                
                
                dx = target_pos.x - pos.x
                dy = target_pos.y - pos.y
                dist = (dx * dx + dy * dy) ** 0.5

                if dist > 0:
                    intent.move_x = dx / dist
                    intent.move_y = dy / dist
                else:
                    intent.move_x = 0.0
                    intent.move_y = 0.0

            elif FleeAI in comps: #possible later addition
                ai: FleeAI = comps[FleeAI]
                if dist < 100 and dist > 0:
                    intent.move_x = -dx / dist
                    intent.move_y = -dy / dist
                else:
                    intent.move_x = 0.0
                    intent.move_y = 0.0       
