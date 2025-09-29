# Class DungeonScene(Scene)

# actual gameplay scene
# possible fields: world, net, hud, camera, local_player_id...
# possible methods: update(dt): send local inputs -> poll snapshots -> 
# client prediction/reconciliation -> world.update(dt).
# in draw(): render world -> HUD.

# owns a world, registers systems in order, and draws entities

from game.scenes.base import Scene
import pygame
import pytmx
from pygame import Surface, Rect
from game.scene_manager import Scene
from game.core.config import Config
from game.world.world import World
from game.world.components import (
    Transform, Intent, DebugRect, Movement,
    Sprite, AnimationState, Facing, Map
    )
from game.core import resources
from game.world.actors.hero_factory import create as create_hero
from game.world.actors.enemy_factory import create as create_enemy
from game.world.systems.input import InputSystem
from game.world.systems.movement import MovementSystem
from game.world.systems.ai import EnemyAISystem
from game.world.systems.room import Room
from game.world.systems.presentation_mapper import PresentationMapperSystem
from game.world.systems.animation import AnimationSystem
from game.world.systems.collision import CollisionSystem
from game.world.systems.attack import AttackSystem
from game.world.systems.triggers import TriggerSystem


class DungeonScene(Scene):
    def __init__(self) -> None:
        self.world = World()
        self.player_id: int | None = None
        self.active_map = None

        #inits the tiled map, will be hardcoded to whatever "level 1" will be
        map_entity = self.world.new_entity()
        self.world.add(map_entity, Map(
            name="testmap",
            path="assets/maps/testmap.tmx",
            tmx_data=pytmx.load_pygame("assets/maps/testmap.tmx"),
            active=True  # mark this as the active map
        ))

    def enter(self) -> None:
        # define loaded map
        for _, comps in self.world.query(Map):
            mp = comps[Map]
            if mp.active:
                self.active_map = mp.tmx_data
                break
        
        # Spawn player knight entity with components that it will use
        self.player_id = create_hero(self.world, archetype="knight", owner_client_id=None, pos=(Config.WINDOW_W/2 - 16, Config.WINDOW_H/2 - 16))

        #Spawn chort enemy entity with components that it will use
        self.chaser_1_id = create_enemy(self.world, kind="chort", pos=(100, 100), params={"target_id" : self.player_id, "agro_range" :200})

         #Spawn chort enemy entity with components that it will use
        self.chaser_1_id = create_enemy(self.world, kind="big_zombie", pos=(100, 50), params={"target_id" : self.player_id, "agro_range" :200})

        # Load collision rects from the active map

        collision_rects = Room.load_collision_objects(self.active_map, layer_name="collisions")

        self.collision_system = CollisionSystem(self.player_id, collision_rects=collision_rects)

        # Register systems in the order they should run each tick (order matters)
        self.world.systems = [
            InputSystem(self.player_id),
            EnemyAISystem(),
            AttackSystem(),   
            MovementSystem(),
            TriggerSystem(self),
            self.collision_system,
            PresentationMapperSystem(),
            AnimationSystem()
        ]

    # method to release resources
    def exit(self) -> None:
        pass

    # this will be used to handle chat/ui later
    def handle_event(self, event) -> None:
        for system in self.world.systems:
            if hasattr(system, "handle_event"):
                system.handle_event(event)

    # one fixed simulation step, runs all systems in order
    def update(self, dt: float) -> None:
        self.world.update(dt)

    # renders all graphics
    def draw(self, surface: Surface) -> None:
        # fill the screen with background color
        surface.fill(Config.BG_COLOR)

        # find the active map

        # render and draw the map if found
        if self.active_map:
            Room.draw_map(surface, self.active_map)

        # get a list of all entities to render
        render_list = []
        for eid, comps in self.world.query(Transform, Sprite, AnimationState, Facing):
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

        # sort the render list by spr.z to control the draw order
        render_list.sort(key=lambda t: (t[0], t[1], t[2]))
        for _, _, _, img, pos in render_list:
        # sort render list by z-index to control draw order
        render_list.sort(key=lambda t: t[0])
        for _, img, pos in render_list:
            surface.blit(img, pos)

    def change_map(self, new_map_name: str, spawn_x: float = None, spawn_y: float = None):
        map_found = False
        new_map_data = None

        # Check if map already exists
        for _, comps in self.world.query(Map):
            mp = comps[Map]
            if mp.name == new_map_name:
                if mp.tmx_data is None:
                    mp.tmx_data = pytmx.load_pygame(mp.path)
                mp.active = True
                new_map_data = mp.tmx_data
                map_found = True
            else:
                mp.active = False

        # If map doesn't exist, create it
        if not map_found:
            map_entity = self.world.new_entity()
            new_map_data = pytmx.load_pygame(f"assets/maps/{new_map_name}.tmx")
            new_map = Map(
                name=new_map_name,
                path=f"assets/maps/{new_map_name}.tmx",
                tmx_data=new_map_data,
                active=True
            )
            self.world.add(map_entity, new_map)

            # deactivate all others
            for _, comps in self.world.query(Map):
                mp = comps[Map]
                if mp.name != new_map_name:
                    mp.active = False

        # Update active_map reference
        self.active_map = new_map_data

        # Load collision rects for the new map
        self.collision_system.collision_rects = Room.load_collision_objects(self.active_map, layer_name="collisions")

        # Move player to new spawn if provided
        if spawn_x is not None and spawn_y is not None:
            tr = self.world.get(self.player_id, Transform)
            if tr:
                tr.x = spawn_x
                tr.y = spawn_y



                
