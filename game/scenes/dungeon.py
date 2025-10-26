# Class DungeonScene(Scene)

# actual gameplay scene
# possible fields: world, net, hud, camera, local_player_id...
# possible methods: update(dt): send local inputs -> poll snapshots -> 
# client prediction/reconciliation -> world.update(dt).
# in draw(): render world -> HUD.

# owns a world, registers systems in order, and draws entities

from game.scenes.base import Scene
import pygame
from pygame import Surface
from game.core.config import Config

from game.world.world import World
from game.world.components import (
    Transform, Map, OnMap, SpawnPolicy, PlayerTag
    )
from game.world.actors.hero_factory import create as create_hero
from game.world.systems.input import InputSystem
from game.world.systems.movement import MovementSystem
from game.world.systems.ai import EnemyAISystem
from game.world.systems.presentation_mapper import PresentationMapperSystem
from game.world.systems.animation import AnimationSystem
from game.world.systems.collision import CollisionSystem
from game.world.systems.attack import AttackSystem
from game.world.systems.triggers import TriggerSystem
from game.world.systems.render import RenderSystem
from game.world.systems.spawn import SpawnSystem
#from game.world.systems.lifespan import lifeSpanSystem
from game.world.systems.death import death
from game.world.maps.map_index import load_registry, pick
from game.world.maps.map_factory import create_or_activate, resolve_map_hint_to_id

class DungeonScene(Scene):
    def __init__(self, role) -> None:
        self.world = World()
        self.player_id: int | None = None
        self.role = role
        self.render = RenderSystem()

    def enter(self) -> None:
        # initial map, or pick a fixed id 
        load_registry("data/map_registry.json")
        mi = pick(require_all=["tier0"])
        create_or_activate(self.world, mi.id)

        # Spawn player once here (or set SpawnPolicy.spawn_player=True to use blueprint)
        self.player_id = create_hero(
            self.world,
            archetype="knight",
            owner_client_id=None,
            pos=(Config.WINDOW_W/2 - 16, Config.WINDOW_H/2 - 16)
        )
        # Tag player with the active map id
        active_id = None
        for _, comps in self.world.query(Map):
            if comps[Map].active:
                active_id = getattr(comps[Map], "id", None)
                break
        if active_id:
            self.world.add(self.player_id, OnMap(id=active_id))

        # Scene/run policy for SpawnSystem (gameplay)
        e = self.world.new_entity()
        self.world.add(e, SpawnPolicy(
            run_title_spawns=False,
            run_game_spawns=True,
            spawn_player=False,          # already spawned above
            spawn_static_enemies=True,
            spawn_pickups=True,
            spawn_objects=True
        ))

        # Systems in order
        self.world.systems = [
            InputSystem(self.player_id),
            EnemyAISystem(),
            AttackSystem(),
            MovementSystem(),
            TriggerSystem(self),     # calls self.change_map(...)
            CollisionSystem(),       
            PresentationMapperSystem(),
            AnimationSystem(),
            SpawnSystem(),           
           # LifeSpanSystem(),
            death(),

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
        self.render.draw(self.world, surface)

    # called by TriggerSystem() when player hits an exit trigger
    def change_map(self, new_map_name: str, spawn_x: float = None, spawn_y: float = None):
         # Accept registry id or legacy ".tmx" names
        target_id = resolve_map_hint_to_id(new_map_name) or new_map_name
        create_or_activate(self.world, target_id)

        # Move player and retag OnMap
        if self.player_id is not None:
            tr = self.world.get(self.player_id, Transform)
            if tr and spawn_x is not None and spawn_y is not None:
                tr.x = float(spawn_x)
                tr.y = float(spawn_y)

            # flip the player's OnMap to the new id
            om = self.world.get(self.player_id, OnMap)
            if om:
                om.id = target_id
            else:
                self.world.add(self.player_id, OnMap(id=target_id))

