# System that adjusts sprite and animation components based on intent
# adjusts the animation clip type and whether frames need to be mirrored

from game.world.components import Intent, AnimationState, Facing

class PresentationMapperSystem:
    def update(self, world, dt):
        
        # loop through all entities with intent, animationstate, and facing components
        for eid, comps in world.query(Intent, AnimationState, Facing):
            it: Intent = comps[Intent]
            anim: AnimationState = comps[AnimationState]
            face: Facing = comps[Facing]

            # adjust clip type depending on intent to move or not
            # moving = "run", not moving = "idle"
            attacking = it.basic_atk
            moving = abs(it.move_x) > 0.01 or abs(it.move_y) > 0.01

            if attacking:
                if face.direction == "up":
                    new_clip = "attack_up"
                elif face.direction == "down":
                    new_clip = "attack_down"
                else:
                    new_clip = "attack_right"
            else:
                new_clip = "run" if moving else "idle"

            if new_clip != anim.clip:
                anim.clip = new_clip
                anim.time = 0.0
                anim.frame = 0
                anim.changed = True
            