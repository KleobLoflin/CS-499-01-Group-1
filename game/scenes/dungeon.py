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
    Sprite, AnimationState, Facing
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

class DungeonScene(Scene):
    def __init__(self) -> None:
        self.world = World()
        self.player_id: int | None = None

        #inits the tiled map, currently hardcoded to testmap.tmx
        self.world.tmx_data = pytmx.load_pygame("assets/maps/testmap.tmx")

    def enter(self) -> None:
        # Spawn player knight entity with components that it will use
        self.player_id = create_hero(self.world, archetype="knight", owner_client_id=None, pos=(Config.WINDOW_W/2 - 16, Config.WINDOW_H/2 - 16))

        #Spawn chort enemy entity with components that it will use
        self.chaser_1_id = create_enemy(self.world, kind="chort", pos=(100, 100), params={"target_id" : self.player_id, "agro_range" :200})



        # Register systems in the order they should run each tick (order matters)
        self.world.systems = [
            InputSystem(self.player_id),
            EnemyAISystem(),   # <-- AI runs every frame
            MovementSystem(),
            CollisionSystem(self.player_id),
            PresentationMapperSystem(),
            AnimationSystem()
            # later: CollisionSystem(), CombatSystem(), ...
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

        # fill the screen with black
        surface.fill(Config.BG_COLOR)
        # render and draw the map
        # note: anything here is drawn first and will be covered by sprites
        # that are drawn later
        Room.draw_map(surface, self.world.tmx_data)

        # get a list of all entities to render
        render_list = []
        for _, comps in self.world.query(Transform, Sprite, AnimationState, Facing):
            tr = comps[Transform]
            spr = comps[Sprite]
            anim = comps[AnimationState]
            face = comps[Facing]
            
            # get sprite animation data using atlas id and type of animation clip
            # frames = list of .pngs for animation
            # mirror_x = True or False to mirror image
            # origin = the center of the sprite
            frames, _, _, mirror_x, origin = resources.clip_info(spr.atlas_id, anim.clip)

            # if no sprite frames found, exit loop
            if not frames:
                continue
            
            # get frame image to draw
            img = frames[anim.frame]

            # handles which way the sprite is facing
            flip = (face.direction < 0) and mirror_x
            if flip:
                img = pygame.transform.flip(img, True, False)
            
            # get (x, y) position of sprite to draw
            pos = (int(tr.x - origin[0]), int(tr.y - origin[1]))
            render_list.append((spr.z, img, pos))

        # sort the render list by spr.z to control the draw order
        render_list.sort(key=lambda t: t[0])
        for _, img, pos in render_list:
            surface.blit(img, pos)
            
