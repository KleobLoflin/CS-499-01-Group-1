# Class: Menu(Scene)

# Title screen menu, start/pause menu, etc...
# controls game menus and when a player selects an option, tells scene_manager to switch
# to the appropriate scene.

# example: on title screen: if player selects "start", asks scene_manager to swtich to hub scene

from game.scenes.base import Scene
import pygame
from pygame import Surface

from game.scenes.dungeon import DungeonScene
from game.world.world import World
from game.world.components import TitleMenu, SpawnPolicy
from game.world.systems.title_menu import TitleMenuSystem
from game.world.systems.render import RenderSystem
from game.world.systems.animation import AnimationSystem
from game.world.systems.presentation_mapper import PresentationMapperSystem
from game.world.systems.movement import MovementSystem
from game.world.systems.collision import CollisionSystem
from game.world.systems.spawn import SpawnSystem

from game.world.maps.map_index import load_registry, pick
from game.world.maps.map_factory import create_or_activate

class TitleScene(Scene):
    def __init__(self, scene_manager):
        self.sm = scene_manager
        self.world = World()

        # title menu system to run in event handler
        pygame.font.init()
        self.menu_ui = TitleMenuSystem(pygame.font.SysFont("consolas", 20))

        # render system runs in draw function, not with logic systems
        self.render = RenderSystem()

    def enter(self) -> None:
        # Registry once
        load_registry("data/map_registry.json")

        # pick any map tagged "title_ok" (weighted)
        mi = pick(require_all=["title_ok"])
        create_or_activate(self.world, mi.id)

        # title menu singleton
        eid = self.world.new_entity()
        self.world.add(eid, TitleMenu(title="Gate Crashers"))

        # Tell SpawnSystem to run ONLY title spawns (not gameplay)
        cfg = self.world.new_entity()
        self.world.add(cfg, SpawnPolicy(
            run_title_spawns=True,
            run_game_spawns=False,
            spawn_player=False
        ))

        # register logic systems in order
        self.world.systems = [
            PresentationMapperSystem(),
            AnimationSystem(),
            MovementSystem(),
            CollisionSystem(),   
            SpawnSystem(),       
            self.menu_ui,
        ]
    
    def exit(self) -> None:
        pass

    def handle_event(self, event) -> None:
        # Titlemenu system runs in event handler and takes care of input
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
        self.render.draw(self.world, surface)
        self.menu_ui.draw_overlay(self.world, surface)