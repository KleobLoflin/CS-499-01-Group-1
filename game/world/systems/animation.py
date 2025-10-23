# system responsible for updating sprite animation components related to timing
# controls timing between looping animated frames

from game.world.components import Sprite, AnimationState
from game.core import resources

class AnimationSystem:
    def update(self, world, dt):

        # loop through all entities with sprite and animationstate components
        for _, comps in world.query(Sprite, AnimationState):
            spr = comps[Sprite]
            anim = comps[AnimationState]

            # retrieve animation clip info
            frames, fps_def, loop_def, _, _ = resources.clip_info(spr.atlas_id, anim.clip)

            # check if animation frames exist
            if not frames:
                continue

            fps = anim.fps or fps_def

            # check if animation clip type is flagged for change
            if anim.changed:
                anim.changed = False
                # make sure fps/loop are respected on clip change
                if anim.fps == 0.0:
                    anim.loop = loop_def
            
            # adjust time depending on framerate
            anim.time += dt * fps
            n = len(frames)
            if anim.loop:
                anim.frame = int(anim.time) % n
            else:
                anim.frame = min(int(anim.time), n - 1)