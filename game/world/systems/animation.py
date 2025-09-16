from game.world.components import Sprite, AnimationState
from game.core import resources

class AnimationSystem:
    def update(self, world, dt):
        for _, comps in world.query(Sprite, AnimationState):
            spr = comps[Sprite]
            anim = comps[AnimationState]

            frames, fps_def, loop_def, _, _ = resources.clip_info(spr.atlas_id, anim.clip)
            if not frames:
                continue

            fps = anim.fps or fps_def
            if anim.changed:
                anim.changed = False
                # make sure fps/loop are respected on clip change
                if anim.fps == 0.0:
                    anim.loop = loop_def
            
            anim.time += dt * fps
            n = len(frames)
            if anim.loop:
                anim.frame = int(anim.time) % n
            else:
                anim.frame = min(int(anim.time), n - 1)