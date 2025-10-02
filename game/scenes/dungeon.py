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
from game.world.systems.render import RenderSystem
from game.world.systems.gameplay_spawn import GameplaySpawnSystem
from game.maps.registry import load_registry
from game.maps.factory import MapFactory
from game.world.spawn_components import MapLoaded


class DungeonScene(Scene):
    def __init__(self, role) -> None:
        self.world = World()
        self.player_id: int | None = None
        self.active_map = None
        self.role = role
        self.render = RenderSystem()

        # map registry + factory
        self.catalog = load_registry("data/map_registry.json")
        self.factory = MapFactory(self.catalog)
        self.map = None

    def enter(self) -> None:
        # initial map by id
        mi = self.catalog["testmap"]
        inst = self.factory.create(mi.id)

        # activate it
        self.activate_map_instance(inst)
        
        # Spawn player knight entity with components that it will use
        self.player_id = create_hero(self.world, archetype="knight", owner_client_id=None, pos=(Config.WINDOW_W/2 - 16, Config.WINDOW_H/2 - 16))

        # Register systems in the order they should run each tick (order matters)
        self.world.systems = [
            InputSystem(self.player_id),
            EnemyAISystem(),
            AttackSystem(),   
            MovementSystem(),
            TriggerSystem(self),
            CollisionSystem(collision_rects=inst.collisions),
            PresentationMapperSystem(),
            AnimationSystem(),
            GameplaySpawnSystem()
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
        self.render.draw(self.world, surface, self.active_map)

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

def activate_map_instance(self, inst):
    self.active_map = inst.tmx

                
