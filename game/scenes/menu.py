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
from game.world.components import TitleMenu
from game.world.systems.title_menu import TitleMenuSystem
from game.world.systems.render import RenderSystem
from game.world.systems.animation import AnimationSystem
from game.world.systems.presentation_mapper import PresentationMapperSystem
from game.world.systems.movement import MovementSystem
from game.world.systems.collision import CollisionSystem
from game.world.systems.room import Room
from game.world.systems.spawn import SpawnSystem
from game.world.maps.registry import load_registry, pick_random
from game.world.maps.map_factory import MapFactory

class TitleScene(Scene):
    def __init__(self, scene_manager):
        self.sm = scene_manager
        self.world = World()

        # map info
        self.catalog = load_registry("data/map_registry.json")
        self.factory = MapFactory(self.catalog)
        self.active_map = None

        # UI
        pygame.font.init()
        self.menu_ui = TitleMenuSystem(pygame.font.SysFont("consolas", 20))

        # render system ran in draw function, not with logic systems
        self.render = RenderSystem()

    def enter(self) -> None:
        # choose any map tagged "title_ok"
        mi = pick_random(self.catalog, require_tags=["title_ok"])
        self.active_map = self.factory.create(mi.id)

        # title menu singleton
        eid = self.world.new_entity()
        self.world.add(eid, TitleMenu(title=self.active_map.name))

        # Emit MapLoaded so TitleSpawnSystem can react
        ml = self.world.new_entity()
        self.world.add(ml, MapLoaded(map_id=self.active_map.id, blueprint=self.active_map.blueprint))

        # register logic systems in order
        self.world.systems = [
            PresentationMapperSystem(),
            AnimationSystem(),
            MovementSystem(),
            CollisionSystem(),
            TitleSpawnSystem(),
            self.menu_ui,
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
        self.render.draw(self.world, surface, self.active_map.tmx if self.active_map else None)
        self.menu_ui.draw_overlay(self.world, surface)