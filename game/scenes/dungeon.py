# dungeon.py — role-based scene setup (singleplayer / client / server)

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

from game.world.maps.map_index import load_registry, pick
from game.world.maps.map_factory import create_or_activate, resolve_map_hint_to_id

# ─────────────────────────────────────────────────────────────
# Future networking hooks (to be implemented later)
# from game.net.client import GameClient
# from game.net.server import GameServer
# from game.world.systems.network import NetworkClientSystem, NetworkServerSystem
# ─────────────────────────────────────────────────────────────

def compose_systems(role: str, player_id: int, scene_ref) -> list:
    """
    Build the list of systems based on the current role.
    Keep simulation (game logic) and presentation (visuals/input) separate.
    """

    # ───── COMMON (all roles) ─────
    systems = [
        # All roles may eventually load shared map data, spawn blueprints, etc.
        TriggerSystem(scene_ref),
        SpawnSystem()
    ]

    # ───── SERVER or SINGLEPLAYER (simulation logic) ─────
    if role in ("server", "single"):
        systems.extend([
            EnemyAISystem(),
            AttackSystem(),
            MovementSystem(),
            CollisionSystem(),
            # TODO: Add future HealthSystem, CombatSystem, SnapshotBuilderSystem
        ])

    # ───── CLIENT or SINGLEPLAYER (presentation & input) ─────
    if role in ("client", "single"):
        systems.extend([
            InputSystem(player_id),
            PresentationMapperSystem(),
            AnimationSystem(),
            # TODO: Add future NetworkClientSystem, AudioSystem, InterpolationSystem
        ])

    return systems


class DungeonScene(Scene):
    def __init__(self, role: str) -> None:
        """
        role: "single", "server", or "client"
        """
        self.world = World()
        self.player_id: int | None = None
        self.role = role
        self.render = RenderSystem()
        self.net = None  # placeholder for client/server connection

    def enter(self) -> None:
        # ───── Map setup ─────
        load_registry("data/map_registry.json")
        mi = pick(require_all=["tier0"])
        create_or_activate(self.world, mi.id)

        # ───── Player setup ─────
        self.player_id = create_hero(
            self.world,
            archetype="knight",
            owner_client_id=None,
            pos=(Config.WINDOW_W / 2 - 16, Config.WINDOW_H / 2 - 16)
        )

        # Tag player with the current map ID
        active_id = None
        for _, comps in self.world.query(Map):
            if comps[Map].active:
                active_id = getattr(comps[Map], "id", None)
                break
        if active_id:
            self.world.add(self.player_id, OnMap(id=active_id))

        # ───── Spawn policy entity ─────
        e = self.world.new_entity()
        self.world.add(e, SpawnPolicy(
            run_title_spawns=False,
            run_game_spawns=True,
            spawn_player=False,
            spawn_static_enemies=True,
            spawn_pickups=True,
            spawn_objects=True
        ))

        # ───── Compose systems based on role ─────
        self.world.systems = compose_systems(self.role, self.player_id, self)

        # ───── TODOs for future networking integration ─────
        # if self.role == "server":
        #     self.net = GameServer()
        #     self.net.start()
        #
        # elif self.role == "client":
        #     self.net = GameClient()
        #     self.net.connect()

    def exit(self) -> None:
        # Clean up network if active
        if self.net:
            # TODO: graceful disconnect
            self.net = None

    def handle_event(self, event) -> None:
        for system in self.world.systems:
            if hasattr(system, "handle_event"):
                system.handle_event(event)

    def update(self, dt: float) -> None:
        # TODO: for client role, poll network snapshots here
        self.world.update(dt)

    def draw(self, surface: Surface) -> None:
        if self.role in ("client", "single"):
            self.render.draw(self.world, surface)

    def change_map(self, new_map_name: str, spawn_x: float = None, spawn_y: float = None):
        target_id = resolve_map_hint_to_id(new_map_name) or new_map_name
        create_or_activate(self.world, target_id)

        if self.player_id is not None:
            tr = self.world.get(self.player_id, Transform)
            if tr and spawn_x is not None and spawn_y is not None:
                tr.x = float(spawn_x)
                tr.y = float(spawn_y)

            om = self.world.get(self.player_id, OnMap)
            if om:
                om.id = target_id
            else:
                self.world.add(self.player_id, OnMap(id=target_id))
