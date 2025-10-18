import pygame
from pygame import Surface
from typing import Optional
from game.world.components import (
    Transform, Sprite, AnimationState, Facing, Map, ActiveMapId, OnMap
)
from game.world.maps.room import Room
from game.core.config import Config
from game.core import resources


class RenderSystem:
    def draw(self, world, surface: Surface) -> None:
        surface.fill(Config.BG_COLOR)

        # find active map id and get tmx data
        active_id: Optional[str] = None
        for _, comps in world.query(ActiveMapId):
            active_id = comps[ActiveMapId].id
            break

        tmx_data = None
        for _, comps in world.query(Map):
            m = comps[Map]
            if (active_id is None and m.active) or (active_id is not None and m.id == active_id):
                tmx_data = m.tmx_data
                break

        if tmx_data is None:
            return  # no map to draw

        # get a list of all entities to render
        render_list = []
        for eid, comps in world.query(Transform, Sprite, AnimationState, Facing):
            
            # filter to active map if OnMap tags are present
            if active_id is not None:
                om = comps.get(OnMap)
                if om is not None and om.id != active_id:
                    continue

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
            img = frames[anim.frame % len(frames)]

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

        # pass entities + map to unified Room drawing
        # note: The new layering and sorting logic happens inside Room.draw_map()
        Room.draw_map(surface, tmx_data, render_list)
