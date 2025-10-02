import pygame
from pygame import Surface
from typing import Optional
from game.world.components import Transform, Sprite, AnimationState, Facing
from game.world.systems.room import Room
from game.core.config import Config
from game.core import resources

class RenderSystem:
    def draw(self, world, surface: Surface, tmx_data: Optional[object]) -> None:
        surface.fill(Config.BG_COLOR)

        if tmx_data is not None:
            Room.draw_map(surface, tmx_data)

        # get a list of all entities to render
        render_list = []
        for eid, comps in world.query(Transform, Sprite, AnimationState, Facing):
            tr = comps[Transform]
            spr = comps[Sprite]
            anim = comps[AnimationState]
            face = comps[Facing]

            # get sprite animation data using atlas id and type of animation clip
            frames, _, _, mirror_x, origin = resources.clip_info(spr.atlas_id, anim.clip)

            # if no sprite frames found, skip this entity
            if not frames:
                continue
            
            # get frame image to draw
            img = frames[anim.frame]

            # handles which way the sprite is facing
            flip = (face.direction == "left") and mirror_x
            if flip:
                img = pygame.transform.flip(img, True, False)
            
            # make attack up and down mirror every other attack
            # ...
            
            # get (x, y) position of sprite to draw
            # calculate position to draw the sprite
            pos = (int(tr.x - origin[0]), int(tr.y - origin[1]))

            # get depth
            depth_y = int(tr.y)
            render_list.append((spr.z, depth_y, eid, img, pos))

        # sort the render list by z-index and depth_y
        render_list.sort(key=lambda t: (t[0], t[1], t[2]))

        # draw all sprites
        for _, _, _, img, pos in render_list:
            surface.blit(img, pos)
