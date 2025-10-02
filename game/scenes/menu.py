# Class: Menu(Scene)

# Title screen menu, start/pause menu, etc...
# controls game menus and when a player selects an option, tells scene_manager to switch
# to the appropriate scene.

# example: on title screen: if player selects "start", asks scene_manager to swtich to hub scene

from game.scenes.base import Scene
import random
import pygame
from pygame import Surface
from game.scenes.dungeon import DungeonScene
from game.world.world import World
from game.world.title_components import TitleMenu
from game.world.systems.title_menu import TitleMenuSystem
from game.world.systems.render import RenderSystem
from game.world.systems.animation import AnimationSystem
from game.world.systems.presentation_mapper import PresentationMapperSystem
from game.world.systems.movement import MovementSystem
from game.world.systems.collision import CollisionSystem
from game.world.systems.room import Room
from game.world.spawn_components import MapLoaded
from game.world.systems.title_spawn import TitleSpawnSystem
from game.maps.registry import load_registry, pick_random
from game.maps.factory import MapFactory

class TitleScene(Scene):
    def __init__(self, scene_manager):
        self.sm = scene_manager
        self.world = World()

        # map info
        self.catalog = load_registry("data/map_registry.json")
        self.factory = MapFactory(self.catalog)
        self.map = None

        # logic systems
        self.present = PresentationMapperSystem()
        self.anim = AnimationSystem()
        self.move = MovementSystem()
        self.collision = CollisionSystem(self.factory.collisions)
        self.spawn = TitleSpawnSystem()

        # render system
        self.render = RenderSystem()

        # UI
        pygame.font.init()
        self.menu_ui = TitleMenuSystem(pygame.font.SysFont("consolas", 20))

        

    def enter(self) -> None:
        # choose any map tagged "title_ok"
        mi = pick_random(self.catalog, require_tags=["title_ok"])
        self.map = self.factory.create(mi.id)

        # title menu singleton
        eid = self.world.new_entity()
        self.world.add(eid, TitleMenu(title=self.map.name))

        # Emit MapLoaded so TitleSpawnSystem can react
        ml = self.world.new_entity()
        self.world.add(ml, MapLoaded(map_id=self.map.id, blueprint=self.map.blueprint))

        # register systems in order
        self.world.systems = [
            self.present,
            self.anim,
            self.move,
            self.collision,
            self.spawn,
            self.menu_ui
        ]

        # music stuff here or probably make an audio system
    
    def exit(self) -> None:
        pass

    def handle_event(self, event) -> None:
        self.menu_ui.handle_event(self.world, event)

    def update(self, dt: float) -> None:
        self.world.update(dt)

        # if player chose a role, swap scenes
        for _, comps in self.world.query(TitleMenu):
            menu: TitleMenu = comps[TitleMenu]

            if menu.selected_role:
                self.sm.set(DungeonScene(role=menu.selected_role))
                return
    
    def draw(self, surface: Surface) -> None:
        self.render.draw(self.world, surface, self.map.tmx if self.map else None)
        self.menu_ui.draw_overlay(self.world, surface)