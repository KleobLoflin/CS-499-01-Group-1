from game.world.components import Intent, AnimationState, Facing

class PresentationMapperSystem:
    def update(self, world, dt):
        for eid, comps in world.query(Intent, AnimationState, Facing):
            it = comps[Intent]
            anim = comps[AnimationState]
            face = comps[Facing]

            moving = abs(it.move_x) > 0.01 or abs(it.move_y) > 0.01
            new_clip = "run" if moving else "idle"

            if new_clip != anim.clip:
                anim.clip = new_clip
                anim.time = 0.0
                anim.frame = 0
                anim.changed = True
            
            # facing
            if it.move_x > 0.01:
                face.direction = 1
            elif it.move_x < -0.01:
                face.direction = -1