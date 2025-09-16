# Class DungeonScene(Scene)

# actual gameplay scene
# possible fields: world, net, hud, camera, local_player_id...
# possible methods: update(dt): send local inputs -> poll snapshots -> 
# client prediction/reconciliation -> world.update(dt).
# in draw(): render world -> HUD.

# currently owns a world, registers systems in order, and draws entities

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
        self.chaser_1_id = create_enemy(self.world, kind="chort", pos=(100, 100), params={"target_id" : self.player_id})

        # Register systems in the order they should run each tick (order matters)
        self.world.systems = [
            InputSystem(self.player_id),
            EnemyAISystem(),   # <-- AI runs every frame
            MovementSystem(),
            PresentationMapperSystem(),
            AnimationSystem()
            # later: CollisionSystem(), CombatSystem(), ...
        ]

    # method to release resources
    def exit(self) -> None:
        pass

    # this will be used to handle chat/ui later
    def handle_event(self, event) -> None:
        pass 

    # one fixed simulation step, runs all systems in order
    def update(self, dt: float) -> None:
        self.world.update(dt)

    def draw(self, surface: Surface) -> None:
        surface.fill(Config.BG_COLOR)
        Room.draw_map(surface, self.world.tmx_data)

        render_list = []
        for _, comps in self.world.query(Transform, Sprite, AnimationState, Facing):
            tr = comps[Transform]
            spr = comps[Sprite]
            anim = comps[AnimationState]
            face = comps[Facing]
            
            frames, _, _, mirror_x, origin = resources.clip_info(spr.atlas_id, anim.clip)

            if not frames:
                continue

            img = frames[anim.frame]
            flip = (face.direction < 0) and mirror_x
            if flip:
                img = pygame.transform.flip(img, True, False)
            
            pos = (int(tr.x - origin[0]), int(tr.y - origin[1]))
            render_list.append((spr.z, img, pos))

        render_list.sort(key=lambda t: t[0])
        for _, img, pos in render_list:
            surface.blit(img, pos)
            
