# AUTHORED BY: Colin Adams, Scott Petty, Nicholas Loflin
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
    Transform, Map, ActiveMapId, OnMap, SpawnPolicy, LocalControlled,
    SpawnRequest, Owner, PlayerTag, NetIdentity, NetHostState,
    NetClientState, MapSpawnState
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
from game.world.systems.camera_spawn import EnsureCameraSystem
from game.world.systems.camera_bootstrap import CameraBootstrapSystem
from game.world.systems.camera_follow import CameraFollowSystem
from game.world.systems.camera_clamp import CameraClampSystem
from game.world.systems.lifespan import LifeSpanSystem
from game.world.systems.death import death
from game.world.systems.sound import SoundSystem
from game.world.systems.scoring import ScoringSystem
from game.world.systems.hud_render import HudRenderSystem
from game.world.systems.projectile import ProjectileSpawnSystem

# net
from game.world.systems.net_host import NetHostSystem
from game.world.systems.net_client import NetClientSystem
from game.world.systems.net_smoothing import NetSmoothingSystem
from game.net.context import net
from game.net.server import NetServer
from game.net.client import NetClient
from game.net.protocol import MSG_START_GAME


from game.world.maps.map_index import load_registry, pick, info
from game.world.maps.map_blueprint import build_Map_component
from game.world.maps.map_factory import create_or_activate, resolve_map_hint_to_id

class DungeonScene(Scene):
    def __init__(self, role, spawn_requests: list[SpawnRequest] | None = None) -> None:
        self.world = World()
        self.role = role.upper()
        self.render = RenderSystem()
        self.hud = HudRenderSystem()
        self.spawn_requests: list[SpawnRequest] = spawn_requests or []
        self.player_id: int | None = None
        net.role = self.role

    def enter(self) -> None:
        # initial map, or pick a fixed id 
        load_registry("data/map_registry.json")
        map_id = net.lobby_data.get("map_id") if isinstance(net.lobby_data, dict) else None
        if map_id is None:
            mi = pick(require_all=["tier1"])
            map_id = mi.id
        create_or_activate(self.world, map_id)

        # Scene/run policy for SpawnSystem (gameplay)
        has_lobby_spawns = bool(self.spawn_requests)
        spawn_player = (self.role == "SOLO" and not has_lobby_spawns)

        e = self.world.new_entity()
        self.world.add(e, SpawnPolicy(
            run_title_spawns=False,
            run_game_spawns=True,
            spawn_player=spawn_player,          
            spawn_static_enemies=True,
            spawn_pickups=True,
            spawn_objects=True
        ))

        # Systems
        if self.role in ("HOST", "SOLO"):
            self.world.systems = [
                SpawnSystem(),
                InputSystem(),
                EnemyAISystem(),
                AttackSystem(),
                MovementSystem(),
                TriggerSystem(self),     # calls self.change_map(...)
                CollisionSystem(),       
                PresentationMapperSystem(),
                AnimationSystem(),
                EnsureCameraSystem(),
                CameraBootstrapSystem(),
                CameraFollowSystem(),
                CameraClampSystem(),
                SoundSystem(),  
                LifeSpanSystem(),
                ScoringSystem(),
                death(),
                ProjectileSpawnSystem(),
            ]
            if self.role == "HOST":
                self._attach_host_net_singleton()
        elif self.role == "CLIENT":
            self.world.systems = [
                InputSystem(),
                NetSmoothingSystem(),
                AnimationSystem(),
                EnsureCameraSystem(),
                CameraBootstrapSystem(),
                CameraFollowSystem(),
                CameraClampSystem(),
                SoundSystem(),
                LifeSpanSystem(),
                death(),
                
                ProjectileSpawnSystem(),
            ]
            self._attach_client_net_singleton()
        else : # fallback to SOLO
            self.world.systems = [
                SpawnSystem(),
                InputSystem(),
                EnemyAISystem(),
                AttackSystem(),
                MovementSystem(),
                TriggerSystem(self),
                CollisionSystem(),
                PresentationMapperSystem(),
                AnimationSystem(),
                EnsureCameraSystem(),
                CameraBootstrapSystem(),
                CameraFollowSystem(),
                CameraClampSystem(),
                SoundSystem(),
                LifeSpanSystem(),
                death(),
                
            ]

        # Spawn players
        if self.role == "SOLO":
            if self.spawn_requests:
                self._spawn_players_from_spawn_requests()
        elif self.role in ("HOST", "CLIENT"):
            self._spawn_players_from_net_lobby()

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
        self.hud.draw(self.world, surface) 

    # Map transitions ############################################################################
    def _ensure_map_loaded(self, map_id: str) -> None:
        # ensure that a Map entity for map_id exists in this world
        # if map is already present return
        for _eid, comps in self.world.query(Map):
            mp: Map = comps[Map]
            if getattr(mp, "id", None) == map_id:
                return
        
        # build a new Map + MapSpawnState, but leave ActiveMapId alone
        mi = info(map_id)
        map_eid = self.world.new_entity()
        self.world.add(map_eid, build_Map_component(mi))
        self.world.add(map_eid, MapSpawnState())

    # called by TriggerSystem() when a player hits an exit trigger
    def change_map_for_entity(
            self,
            entity_id: int,
            new_map_name: str,
            spawn_x: float | None = None,
            spawn_y: float | None = None,
    ) -> None:
        # move a specific player entity to a new map
        # update ActiveMapId and Map.active for the local player on this machine
        # ensure the target map is loaded and update that entities OnMap for remote players

        # Accept registry id or legacy ".tmx" names
        target_id = resolve_map_hint_to_id(new_map_name) or new_map_name

        # check if this entity is local-controlled
        is_local = self.world.get(entity_id, LocalControlled) is not None
        if is_local:
            # for local player, this machine's active map becomes target_id
            create_or_activate(self.world, target_id)
            # remember which entity is the local player in case player_id is still needed somewhere
            self.player_id = entity_id
        else:
            # for remote player, make sure map exists without changing
            # ActiveMapId or Map.active flags
            self._ensure_map_loaded(target_id)

        # reposition the entity
        tr = self.world.get(entity_id, Transform)
        if tr is not None and spawn_x is not None and spawn_y is not None:
            tr.x = float(spawn_x)
            tr.y = float(spawn_y)

        # update/attach OnMap
        om = self.world.get(entity_id, OnMap)
        if om:
            om.id = target_id
        else:
            self.world.add(entity_id, OnMap(id=target_id))
    
    # for backwards compatibility with old system
    def change_map(self, new_map_name: str, spawn_x: float = None, spawn_y: float = None):
        if self.player_id is None:
            return
        self.change_map_for_entity(self.player_id, new_map_name, spawn_x, spawn_y)
         
    # Spawning helpers ##########################################################################

    def _find_active_map_and_spawn_pos(self) -> tuple[str | None, float, float]:
        # Find active map id
        active_id = None
        for _, comps in self.world.query(ActiveMapId):
            active_id = comps[ActiveMapId].id
            break

        bp = None
        for _, comps in self.world.query(Map):
            mp = comps[Map]
            if active_id is None or getattr(mp, "id", None) == active_id:
                bp = getattr(mp, "blueprint", None)
                break

        base_x = Config.WINDOW_W / 2
        base_y = Config.WINDOW_H / 2

        # If the map blueprint has game_spawns.player_start.pos, use that
        if isinstance(bp, dict):
            gs = bp.get("game_spawns", {})
            ps = gs.get("player_start")
            if isinstance(ps, dict) and "pos" in ps:
                try:
                    sx, sy = ps["pos"]
                    base_x = float(sx)
                    base_y = float(sy)
                except Exception:
                    pass

        return active_id, base_x, base_y
    
    def _spawn_players_from_spawn_requests(self) -> None:
        """
        SOLO mode: consume self.spawn_requests (from HubScene) and spawn heroes accordingly.
        - hero_key: "hero.knight_blue", etc.
        - is_local: whether to attach LocalControlled and store player_id.
        - net_id: peer id for networking (unused in SOLO).
        """
        active_id, base_x, base_y = self._find_active_map_and_spawn_pos()
        count = len(self.spawn_requests)
        if count <= 0:
            return

        # Spread players horizontally around the base position
        spacing = 16.0
        start_offset = -spacing * (count - 1) / 2.0

        for i, req in enumerate(self.spawn_requests):
            hero_key = req.hero_key  # "hero.knight_blue"
            if "." in hero_key:
                archetype = hero_key.split(".", 1)[1]
            else:
                archetype = hero_key

            x = base_x + start_offset + spacing * i
            y = base_y

            eid = create_hero(self.world, archetype=archetype,
                              owner_client_id=req.net_id, pos=(x, y))

            # Tag with OnMap so RenderSystem shows them on the active map
            if active_id is not None:
                self.world.add(eid, OnMap(id=active_id))

            # Mark local-controlled player
            if req.is_local:
                self.world.add(eid, LocalControlled())
                self.player_id = eid

    def _spawn_players_from_net_lobby(self) -> None:
        """
        HOST/CLIENT: spawn heroes based on net.lobby_data["heroes"] mapping.
        Both host and clients run this so that all machines have matching hero
        entities; host is authoritative for simulation, clients treat them as
        proxies and get their updated positions from snapshots.
        """
        heroes_by_peer = {}
        if isinstance(net.lobby_data, dict):
            heroes_by_peer = net.lobby_data.get("heroes", {}) or {}
        if not heroes_by_peer:
            # Fallback: just spawn local player
            heroes_by_peer = {net.my_peer_id: "hero.knight_blue"}

        active_id, base_x, base_y = self._find_active_map_and_spawn_pos()
        count = len(heroes_by_peer)
        spacing = 32.0
        start_offset = -spacing * (count - 1) / 2.0

        for i, (peer_id, hero_key) in enumerate(heroes_by_peer.items()):
            if "." in hero_key:
                archetype = hero_key.split(".", 1)[1]
            else:
                archetype = hero_key

            x = base_x + start_offset + spacing * i
            y = base_y

            eid = create_hero(
                self.world,
                archetype=archetype,
                owner_client_id=peer_id,
                pos=(x, y),
            )

            # Tag with OnMap so RenderSystem shows them on the active map
            if active_id is not None:
                self.world.add(eid, OnMap(id=active_id))

            # Owner(peer_id) is added in hero_factory via owner_client_id,
            # so we don't have to add it manually here.

            if peer_id == net.my_peer_id:
                # Mark local-controlled player on this machine
                self.world.add(eid, LocalControlled())
                self.player_id = eid

    # networking ###############################################################
    def _attach_host_net_singleton(self) -> None:
        """Create or reuse the host UDP server and attach NetHostState."""
        # Create server only once per run:
        if net.server is None:
            #  port 
            net.server = NetServer(port=5000)
            net.my_peer_id = "host"

        # Attach ECS components
        e = self.world.new_entity()
        self.world.add(e, NetIdentity(my_peer_id=net.my_peer_id, role="HOST"))
        self.world.add(e, NetHostState(
            server=net.server,
            peers=net.peers,
        ))

        self.world.systems.append(NetHostSystem())

    def _attach_client_net_singleton(self) -> None:
        """Attach NetClientState to the existing NetClient that was created in HubScene"""
        # HubScene(JOIN) already created net.client and did the HELLO/WELCOME handshake.
        # If that didn't happen, we can't safely connect here
        if net.client is None:
            print("[DungeonScene] Warning: net.client is None; "
                  "Client must join via HubScene first.")
            return
        
        # If there is still not a peer id, mark as pending
        if not net.my_peer_id:
            net.my_peer_id = "client_pending"

        e = self.world.new_entity()
        self.world.add(e, NetIdentity(my_peer_id=net.my_peer_id, role="CLIENT"))
        self.world.add(e, NetClientState(client=net.client))

        # NetClientSystem runs before animation/render
        for idx, sys in enumerate(self.world.systems):
            if isinstance(sys, InputSystem):
                self.world.systems.insert(idx + 1, NetClientSystem())
