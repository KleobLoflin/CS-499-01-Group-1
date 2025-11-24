import pygame
from pygame import Surface
from typing import Optional
from game.world.components import (
    Transform, Sprite, AnimationState, Facing, Map, ActiveMapId, OnMap, Camera
)
from game.world.maps.room import Room
from game.core.config import Config
from game.core import resources


class RenderSystem:
    def draw(self, world, surface: Surface) -> None:
        # find active map id and get tmx data
        active_id: Optional[str] = None
        for _, comps in world.query(ActiveMapId):
            active_id = comps[ActiveMapId].id
            break

        # get camera
        cam = None
        for _, comps in world.query(Camera):
            cam = comps[Camera]
            break

        # get a list of all entities to render
        entities_world = []
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
            entities_world.append((spr.z, depth_y, eid, img, pos))

        # get tmx data if it exists
        tmx_data = None
        for _, comps in world.query(Map):
            m = comps[Map]
            if (active_id is None and m.active) or (active_id is not None and m.id == active_id):
                tmx_data = m.tmx_data
                break
        
        # if no tmx data draw entities only and don't clear surface
        if tmx_data is None:
            # z and y-depth sort
            entities_world.sort(key=lambda d: (d[0], d[1]))
            for _, _, _, img, pos in entities_world:
                surface.blit(img, pos)
            return
        
        # pass entities + map to unified Room drawing
        surface.fill(Config.BG_COLOR)
        
        if cam is not None:
            view_left = cam.x - cam.viewport_w // 2
            view_top  = cam.y - cam.viewport_h // 2
            Room.draw_map_view(surface, tmx_data, entities_world,
                               view_left, view_top, cam.viewport_w, cam.viewport_h)
        else:
            # Fallback: no camera; draw whole map as before
            Room.draw_map(surface, tmx_data, entities_world)
        
