# AUTHORED BY: Scott Petty
# game/scenes/hub.py
#
# HubScene(Scene)
#
# Lobby / character-select screen for:
#   - SINGLE: local character select then straight to DungeonScene
#   - HOST:   host owns the lobby, clients join slots, host presses ready to start
#   - JOIN:   client browses hosts, joins a lobby, picks a character, and readies up
#
# This scene:
#   - Uses the "hub" map for a background via the usual map pipeline.
#   - Manages LobbyState + LobbySlot components for up to 5 players.
#   - Spawns animated hero preview entities in 5 columns.
#   - When ready, builds SpawnRequest components and hands them to DungeonScene.
#

from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any

import pygame
from pygame import Surface

from game.scenes.base import Scene
from game.scenes.dungeon import DungeonScene
from game.core.config import Config

from game.world.world import World
from game.world.components import (
    LobbyState, LobbySlot, AvailableHosts,
    NetIdentity, Owner, SpawnRequest,
    PlayerTag, LocalControlled,
    Transform, Facing, Sprite, AnimationState,
    SoundRequest,
)
from game.world.actors.hero_factory import create as create_hero
from game.world.systems.animation import AnimationSystem
from game.world.systems.render import RenderSystem
from game.world.systems.sound import SoundSystem

from game.net.context import net
from game.net.discovery import HostDiscovery, ClientDiscovery
from game.net.server import NetServer
from game.net.client import NetClient
from game.net.protocol import (
    PROTOCOL_VERSION,
    MSG_HELLO,
    MSG_WELCOME,
    MSG_JOIN_DENY,
    MSG_LOBBY_UPDATE,
    MSG_LOBBY_STATE,
    MSG_START_GAME,
)

class HubScene(Scene):
    # mode = "Single" | "Host" | "Join"

    HERO_CATALOG: List[str] = [
        "knight_blue",
        "knight_green",
        "knight_red",
        "knight_yellow",
        "knight_purple",
    ]

    def __init__(self, scene_manager, mode: str = "SINGLE", role: str | None = None) -> None:
        self.scene_manager = scene_manager

        effective = role if role is not None else mode
        effective = (effective or "SINGLE").upper()

        if effective in ("SINGLE", "SINGLEPLAYER", "SP"):
            self.mode = "SINGLE"
        elif effective in ("HOST", "SERVER"):
            self.mode = "HOST"
        elif effective in ("JOIN", "CLIENT"):
            self.mode = "JOIN"
        else:
            self.mode = "SINGLE"

        self.world = World()

        # systems
        self.world.systems = [
            AnimationSystem(),
            SoundSystem(),
        ]
        self.render_system = RenderSystem()

        # font
        pygame.font.init()
        self.font = pygame.font.Font("assets/fonts/Retro Gaming.ttf", 16)

        # player slot images
        self.slot_normal_img = pygame.image.load("assets/ui/hub_screen/hub_slot_normal.png").convert_alpha()
        self.slot_ready_img = pygame.image.load("assets/ui/hub_screen/hub_slot_ready.png").convert_alpha()

        self.slot_w = self.slot_normal_img.get_width()
        self.slot_h = self.slot_normal_img.get_height()

        # Net identity
        if self.mode == "SINGLE":
            self.peer_id = "solo"
            self.role = "SOLO"
        elif self.mode == "HOST":
            self.peer_id = "host"
            self.role = "HOST"
        else:
            self.peer_id = "client"
            self.role = "CLIENT"
        
        # net context
        net.role = self.role
        net.my_peer_id = self.peer_id

        # discovery
        self.host_discovery: HostDiscovery | None = None
        self.client_discovery: ClientDiscovery | None = None

    # -------------------------------------------------------------------------
    # Scene life cycle
    # -------------------------------------------------------------------------

    def enter(self) -> None:

        # Create NetIdentity singleton
        e_net = self.world.new_entity()
        self.world.add(e_net, NetIdentity(my_peer_id=self.peer_id, role=self.role))

        # Create LobbyState singleton
        lobby_e = self.world.new_entity()
        substate = "BROWSER" if self.mode == "JOIN" else "SELECT"
        lobby_state = LobbyState(
            mode=self.mode,
            substate=substate,
            character_catalog=[f"hero.{name}" for name in self.HERO_CATALOG],
        )
        self.world.add(lobby_e, lobby_state)

        # AvailableHosts singleton for "JOIN" mode
        if self.mode == "JOIN":
            self.world.add(lobby_e, AvailableHosts())

        # Create up to 5 LobbySlot entities
        # Slot assignment policy:
        #   SINGLE: slot 0 is local.
        #   HOST:   slot 0 is local host; others wait for remote peers.
        #   JOIN:   no local slot yet; becomes available when we "join" a host lobby.
        for i in range(5):
            is_local = (self.mode in ("SINGLE", "HOST") and i == 0)
            peer_id = self.peer_id if is_local else None
            name = f"Player {i + 1}"

            e_slot = self.world.new_entity()
            slot = LobbySlot(
                index=i,
                player_eid=None,
                is_local=is_local,
                selected_char_index=0,
                ready=False,
                name=name,
                preview_eid=None,
                peer_id=peer_id,
            )
            self.world.add(e_slot, slot)

            if is_local:
                self._refresh_slot_preview(e_slot, slot)

        # networking setup
        if self.mode == "HOST":
            self._init_host_network()
        elif self.mode == "JOIN":
            pass

        # discovery
        if self.mode == "HOST":
            # start discovery responder
            self.host_discovery = HostDiscovery(game_port=5000, name="GateCrashers Host")
        elif self.mode == "JOIN":
            # start discovery broadcaster
            self.client_discovery = ClientDiscovery()

    def exit(self) -> None:
        # stop discovery sockets
        if self.host_discovery is not None:
            self.host_discovery.close()
            self.host_discovery = None
        if self.client_discovery is not None:
            self.client_discovery.close()
            self.client_discovery = None
        pass

    # -------------------------------------------------------------------------
    # Event handling
    # -------------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            return

        if event.type != pygame.KEYDOWN:
            return

        key = event.key

        # ESC -> go back to title
        if key == pygame.K_ESCAPE:
            from game.scenes.menu import TitleScene
            self.scene_manager.set(TitleScene(self.scene_manager))
            return

        lobby_state = self._get_lobby_state()
        if lobby_state is None:
            return

        if self.mode == "JOIN" and lobby_state.substate == "BROWSER":
            self._handle_join_browser_key(lobby_state, key)
            return

        # In SELECT substate we are in the actual multi-column lobby UI.
        if lobby_state.substate == "SELECT":
            self._handle_lobby_select_key(lobby_state, key)

    # -------------------------------------------------------------------------
    # Update & draw
    # -------------------------------------------------------------------------

    def update(self, dt: float) -> None:
        # animation for character previews
        self.world.update(dt)

        # Update previews if anyone changed selection, etc. (no-op most frames)
        self._sync_previews()

        lobby_state = self._get_lobby_state()

        # networking and discovery ################################################
    
        if self.mode == "HOST":
            # host pump game lobby messages and respond to LAN discovery
            self._host_net_pump()
            if self.host_discovery is not None:
                self.host_discovery.update(dt)

        elif self.mode == "JOIN":
            # client pump lobby messages if connected
            self._client_net_pump()

            # while in browser, send discovery broadcasts and update host list
            if lobby_state is not None and lobby_state.substate == "BROWSER":
                if self.client_discovery is not None:
                    self.client_discovery.update(dt)

                    hosts_comp: Optional[AvailableHosts] = None
                    for _, comps in self.world.query(AvailableHosts):
                        hosts_comp = comps[AvailableHosts]
                        break

                    if hosts_comp is not None:
                        # fill hosts list from discovery ["ip:port", ...]
                        hosts_comp.hosts = [
                            f"{ip}:{port}"
                            for (ip, port), _name in sorted(self.client_discovery.hosts.items())
                        ]

        # transitions ##############################################################################

        if lobby_state and lobby_state.substate == "SELECT":
            # SINGLE
            if self.mode == "SINGLE":
                if self._should_transition_to_dungeon_single():
                    spawn_requests = self._build_spawn_requests()
                    if spawn_requests:
                        # fill lobby_data (Solo)
                        heroes_by_peer = {}
                        for req in spawn_requests:
                            pid = req.net_id or "solo"
                            heroes_by_peer[pid] = req.hero_key
                        net.lobby_data = {
                            "heroes": heroes_by_peer,
                            "map_id": "level1",
                        }

                        next_scene = DungeonScene(role="SOLO", spawn_requests=spawn_requests)
                        self.scene_manager.set(next_scene)
        
            # HOST
            elif self.mode == "HOST":
                if self._all_occupied_slots_ready():
                    self._host_start_networked_game()

            # JOIN: client waits for MSG_START_GAME from host which is handled in _client_net_pump


    def draw(self, surface: Surface) -> None:
        # clear screen
        surface.fill(Config.BG_COLOR)
        
        lobby_state = self._get_lobby_state()
        if lobby_state is None:
            return

        # draw host browser UI if "JOIN"
        if self.mode == "JOIN" and lobby_state.substate == "BROWSER":
            self._draw_join_browser(surface, lobby_state)
            return
        
        # draw player slots
        slots = list(self._iter_slots())
        for _, slot in slots:
            x = slot.index * self.slot_w
            img = self.slot_ready_img if slot.ready else self.slot_normal_img
            surface.blit(img, (x, 0))

        # draw hero previews
        self.render_system.draw(self.world, surface)

        # draw slot labels
        for _, slot in self._iter_slots():
            x = slot.index * self.slot_w
            if slot.peer_id is None and not slot.is_local:
                label = "Waiting..."
            else:
                label = slot.name # OR: f"Player {slot.index + 1}"
            txt = self.font.render(label, True, (255, 255, 255))
            surface.blit(txt, (x + 25, 12))

    # Helpers: Lobby / slots ############################################################

    def _get_lobby_state(self) -> Optional[LobbyState]:
        for _, comps in self.world.query(LobbyState):
            return comps[LobbyState]
        return None

    def _iter_slots(self):
        for eid, comps in self.world.query(LobbySlot):
            yield eid, comps[LobbySlot]

    def _find_local_slot(self) -> Optional[Tuple[int, LobbySlot]]:
        for eid, slot in self._iter_slots():
            if slot.is_local:
                return eid, slot
        return None

    # JOIN browser ########################################################################

    def _handle_join_browser_key(self, lobby_state: LobbyState, key: int) -> None:
        hosts_comp: Optional[AvailableHosts] = None
        for _, comps in self.world.query(AvailableHosts):
            hosts_comp = comps[AvailableHosts]
            break

        if hosts_comp is None:
            return

        # NOTE: hosts_comp is filled by ClientDiscovery in update()

        if key in (pygame.K_UP, pygame.K_w):
            if hosts_comp.hosts:
                hosts_comp.selected_index = max(0, hosts_comp.selected_index - 1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            if hosts_comp.hosts:
                hosts_comp.selected_index = min(
                    len(hosts_comp.hosts) - 1, hosts_comp.selected_index + 1
                )
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            # only attempt join if there is a host
            if not hosts_comp.hosts:
                return
            
            # parse "ip:port"
            entry = hosts_comp.hosts[hosts_comp.selected_index]
            ip = "127.0.0.1"    # placeholders
            port = 5000         #
            if ":" in entry:
                ip_str, port_str = entry.split(":", 1)
                ip = ip_str.strip() or ip
                try:
                    port = int(port_str)
                except ValueError:
                    port = 5000

            # stop discovery when a host is chosen
            if self.client_discovery is not None:
                self.client_discovery.close()
                self.client_discovery = None
            
            # Create NetClient and send HELLO
            # host will reply with WELCOME + LOBBY_STATE
            self._init_client_network(ip, port)
            lobby_state.substate = "SELECT"

    def _configure_joined_slots_for_debug(self) -> None:
        """
        Debug-only helper
        """
        # Clear existing slots
        for eid, slot in list(self._iter_slots()):
            if slot.preview_eid is not None:
                self.world.delete_entity(slot.preview_eid)
            self.world.delete_entity(eid)

        # Rebuild 5 slots
        for i in range(5):
            if i == 0:
                is_local = False
                peer_id = "host"
                name = "Host"
            elif i == 1:
                is_local = True
                peer_id = self.peer_id
                name = "You"
            else:
                is_local = False
                peer_id = None
                name = f"Player {i + 1}"

            e_slot = self.world.new_entity()
            slot = LobbySlot(
                index=i,
                player_eid=None,
                is_local=is_local,
                selected_char_index=0,
                ready=False,
                name=name,
                preview_eid=None,
                peer_id=peer_id,
            )
            self.world.add(e_slot, slot)

            if is_local:
                self._refresh_slot_preview(e_slot, slot)

    # networking HOST ############################################################

    def _init_host_network(self) -> None:
        # Create server socket only once; reuse across scenes
        if net.server is None:
            net.server = NetServer(port=5000)
        net.my_peer_id = "host"

    def _host_net_pump(self) -> None:
        server = net.server
        if server is None:
            return

        for addr, msg in server.recv_all():
            mtype = msg.get("type")

            if mtype == MSG_HELLO:
                self._host_handle_hello(server, addr, msg)
            elif mtype == MSG_LOBBY_UPDATE:
                self._host_handle_lobby_update(msg)
            elif mtype == MSG_START_GAME:
                # Clients should not send this; ignore.
                pass
            elif mtype == MSG_JOIN_DENY:
                # Not expected on host
                pass

    def _host_handle_hello(self, server: NetServer, addr: Tuple[str, int], msg: Dict[str, Any]) -> None:
        # Basic protocol check
        if int(msg.get("protocol", -1)) != PROTOCOL_VERSION:
            server.send_raw(addr, {
                "type": MSG_JOIN_DENY,
                "reason": "protocol_mismatch",
            })
            return

        # Collect currently used peer_ids
        used_peer_ids = [slot.peer_id for _, slot in self._iter_slots() if slot.peer_id is not None]

        # Deny if full
        if len(used_peer_ids) >= 5:
            server.send_raw(addr, {
                "type": MSG_JOIN_DENY,
                "reason": "full",
            })
            return

        # Assign a new peer id
        base = "peer"
        index = 1
        while f"{base}:{index}" in used_peer_ids:
            index += 1
        peer_id = f"{base}:{index}"

        # Find a free slot (not necessarily index 0)
        free_slot_eid = None
        free_slot_comp: Optional[LobbySlot] = None
        for eid, slot in self._iter_slots():
            if slot.peer_id is None and not slot.is_local:
                free_slot_eid = eid
                free_slot_comp = slot
                break

        if free_slot_comp is None:
            server.send_raw(addr, {
                "type": MSG_JOIN_DENY,
                "reason": "full",
            })
            return

        free_slot_comp.peer_id = peer_id
        free_slot_comp.name = f"Player {free_slot_comp.index + 1}"
        free_slot_comp.selected_char_index = 0
        free_slot_comp.ready = False
        self._refresh_slot_preview(free_slot_eid, free_slot_comp)

        # Register mapping in global context (host)
        net.peers[peer_id] = addr
        server.register_peer(peer_id, addr)

        # Send welcome + lobby snapshot
        server.send_raw(addr, {
            "type": MSG_WELCOME,
            "protocol": PROTOCOL_VERSION,
            "peer_id": peer_id,
        })
        server.send_raw(addr, {
            "type": MSG_LOBBY_STATE,
            "slots": self._build_lobby_slots_payload(),
        })

        # Broadcast updated lobby to everyone else
        server.broadcast({
            "type": MSG_LOBBY_STATE,
            "slots": self._build_lobby_slots_payload(),
        })

    def _host_handle_lobby_update(self, msg: Dict[str, Any]) -> None:
        peer_id = msg.get("peer_id")
        if not isinstance(peer_id, str):
            return

        hero_index = msg.get("hero_index")
        ready = msg.get("ready")

        for eid, slot in self._iter_slots():
            if slot.peer_id == peer_id:
                if hero_index is not None:
                    try:
                        hero_index = int(hero_index)
                    except (TypeError, ValueError):
                        hero_index = 0
                    slot.selected_char_index = hero_index % len(self.HERO_CATALOG)
                    self._refresh_slot_preview(eid, slot)
                if ready is not None:
                    slot.ready = bool(ready)
                break

        if net.server:
            net.server.broadcast({
                "type": MSG_LOBBY_STATE,
                "slots": self._build_lobby_slots_payload(),
            })

    def _build_lobby_slots_payload(self) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for _, slot in self._iter_slots():
            payload.append({
                "index": slot.index,
                "peer_id": slot.peer_id,
                "hero_index": slot.selected_char_index,
                "ready": slot.ready,
                "name": slot.name,
            })
        return payload

    def _all_occupied_slots_ready(self) -> bool:
        any_occupied = False
        for _, slot in self._iter_slots():
            if slot.peer_id is not None or slot.is_local:
                any_occupied = True
                if not slot.ready:
                    return False
        return any_occupied

    def _host_start_networked_game(self) -> None:
        """
        Host decides to start the game:
          - Build heroes_by_peer from LobbySlots.
          - Fill net.lobby_data.
          - Broadcast START_GAME.
          - Switch to DungeonScene(HOST).
        """
        heroes_by_peer: Dict[str, str] = {}
        for _, slot in self._iter_slots():
            if slot.peer_id is None and not slot.is_local:
                continue
            hero_name = self.HERO_CATALOG[slot.selected_char_index % len(self.HERO_CATALOG)]
            hero_key = f"hero.{hero_name}"
            pid = slot.peer_id or "host"
            heroes_by_peer[pid] = hero_key

        net.lobby_data = {
            "heroes": heroes_by_peer,
            "map_id": "level1",  # you can pick something else later
        }

        if net.server:
            net.server.broadcast({
                "type": MSG_START_GAME,
                "lobby": net.lobby_data,
            })

        # Host transitions to DungeonScene(HOST)
        self.scene_manager.set(DungeonScene(role="HOST"))

    # networking JOIN ##############################################################

    def _init_client_network(self, host_ip: str, host_port: int) -> None:
        if net.client is None:
            net.client = NetClient(host=host_ip, port=host_port)
            net.my_peer_id = "client_pending"

            net.client.send({
                "type": MSG_HELLO,
                "protocol": PROTOCOL_VERSION,
                "name": "Player",
            })

    def _client_net_pump(self) -> None:
        client = net.client
        if client is None:
            return

        for msg in client.recv_all():
            mtype = msg.get("type")

            if mtype == MSG_WELCOME:
                peer_id = msg.get("peer_id")
                if isinstance(peer_id, str):
                    net.my_peer_id = peer_id
            elif mtype == MSG_LOBBY_STATE:
                slots_payload = msg.get("slots", [])
                self._apply_lobby_slots_payload(slots_payload)
            elif mtype == MSG_START_GAME:
                lobby_payload = msg.get("lobby", {})
                net.lobby_data = lobby_payload
                self.scene_manager.set(DungeonScene(role="CLIENT"))
            elif mtype == MSG_JOIN_DENY:
                # TODO: show error to player
                pass

    def _apply_lobby_slots_payload(self, slots_payload: List[Dict[str, Any]]) -> None:
        # Apply server-authoritative slot mapping.
        # We assume slots_payload has entries for indices 0..4.
        for eid, slot in list(self._iter_slots()):
            data = next((s for s in slots_payload if s.get("index") == slot.index), None)
            if data is None:
                # If host has no info for this slot, treat as empty
                slot.peer_id = None
                slot.ready = False
                slot.selected_char_index = 0
                slot.name = f"Player {slot.index + 1}"
                slot.is_local = False
                # Clear preview
                if slot.preview_eid is not None:
                    self.world.delete_entity(slot.preview_eid)
                    slot.preview_eid = None
                continue

            slot.peer_id = data.get("peer_id")
            slot.ready = bool(data.get("ready", False))
            slot.selected_char_index = int(data.get("hero_index", 0))
            slot.name = f"Player {slot.index + 1}"
            slot.is_local = (slot.peer_id == net.my_peer_id)

            self._refresh_slot_preview(eid, slot)

    def _send_lobby_update_from_client(self, slot: LobbySlot) -> None:
        if net.client is None:
            return
        net.client.send({
            "type": MSG_LOBBY_UPDATE,
            "peer_id": net.my_peer_id,
            "hero_index": slot.selected_char_index,
            "ready": slot.ready,
        })

    # SELECT state input ############################################################### 

    def _handle_lobby_select_key(self, lobby_state: LobbyState, key: int) -> None:
        local = self._find_local_slot()
        if local is None:
            return
        slot_eid, slot = local

        catalog_len = len(self.HERO_CATALOG)

        # UP
        if key in (pygame.K_UP, pygame.K_w):
            slot.selected_char_index = (slot.selected_char_index - 1) % catalog_len
            slot.ready = False
            self._refresh_slot_preview(slot_eid, slot)
            if self.mode == "JOIN":
                self._send_lobby_update_from_client(slot)
            elif self.mode == "HOST":
                # host updates everyone
                if net.server:
                    net.server.broadcast({
                        "type": MSG_LOBBY_STATE,
                        "slots": self._build_lobby_slots_payload(),
                    })
            
            # register sound for character selection change
            slot_comps = self.world.components_of(slot_eid)
            slot_comps[SoundRequest] = SoundRequest(
                event="menu_move",
                global_event=True,
            )

        # DOWN
        elif key in (pygame.K_DOWN, pygame.K_s):
            slot.selected_char_index = (slot.selected_char_index + 1) % catalog_len
            slot.ready = False
            self._refresh_slot_preview(slot_eid, slot)
            if self.mode == "JOIN":
                self._send_lobby_update_from_client(slot)
            elif self.mode == "HOST":
                if net.server:
                    net.server.broadcast({
                    "type": MSG_LOBBY_STATE,
                    "slots": self._build_lobby_slots_payload(),
                })
            
            # register sound for character selection change
            slot_comps = self.world.components_of(slot_eid)
            slot_comps[SoundRequest] = SoundRequest(
                event="menu_move",
                global_event=True,
            )

        # SELECT
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            slot.ready = not slot.ready
            if self.mode == "JOIN":
                self._send_lobby_update_from_client(slot)
            elif self.mode == "HOST":
                if net.server:
                    net.server.broadcast({
                        "type": MSG_LOBBY_STATE,
                        "slots": self._build_lobby_slots_payload(),
                    })
            
            # register sound for character selection change
            slot_comps = self.world.components_of(slot_eid)
            slot_comps[SoundRequest] = SoundRequest(
                event="ready_up",
                global_event=True,
            )

        # Host-only shortcut: R key toggles all non-empty slots to ready 
        elif key == pygame.K_r and self.mode == "HOST":
            for _, s in self._iter_slots():
                if s.peer_id is not None or s.is_local:
                    s.ready = True
            if net.server:
                net.server.broadcast({
                    "type": MSG_LOBBY_STATE,
                    "slots": self._build_lobby_slots_payload(),
                })

    # preview hero entities #################################################################

    def _slot_preview_position(self, index: int) -> Tuple[float, float]:
        # center of the Nth 128 x 360 column
        columns = 5
        x = index * self.slot_w + self.slot_w / 2
        y = Config.WINDOW_H / 2
        return x, y

    def _refresh_slot_preview(self, slot_eid: int, slot: LobbySlot) -> None:
        # Delete existing preview if any
        if slot.preview_eid is not None:
            self.world.delete_entity(slot.preview_eid)
            slot.preview_eid = None
        
        # dont show anything if slot is empty
        if slot.peer_id is None and not slot.is_local:
            return
        
        idx = slot.selected_char_index % len(self.HERO_CATALOG)
        hero_name = self.HERO_CATALOG[idx]
        archetype = hero_name

        x, y = self._slot_preview_position(slot.index)

        eid = create_hero(
            self.world,
            archetype=archetype,
            owner_client_id=slot.peer_id,
            pos=(x, y)
        )

        comps = self.world.components_of(eid)
        anim = comps.get(AnimationState)
        if anim is not None:
            anim.clip = "run"
            anim.frame = 0
            anim.time = 0.0
            anim.changed = True
        
        face = comps.get(Facing)
        if face is not None:
            face.direction = "right"

        slot.preview_eid = eid

    def _sync_previews(self) -> None:
        # Currently a no-op. Left here incase we want to set/check some kind of flags later
        return

    # ready check / spawn requests for SINGLE #############################################################

    def _should_transition_to_dungeon_single(self) -> bool:
        # Only the local slot matters
        local = self._find_local_slot()
        return bool(local and local[1].ready)

    def _build_spawn_requests(self) -> List[SpawnRequest]:
        spawn_requests: List[SpawnRequest] = []
        for _, slot in self._iter_slots():
            if slot.ready and (slot.peer_id is not None or slot.is_local):
                hero_name = self.HERO_CATALOG[slot.selected_char_index % len(self.HERO_CATALOG)]
                hero_key = f"hero.{hero_name}"
                req = SpawnRequest(
                    hero_key=hero_key,
                    is_local=slot.is_local,
                    player_name=slot.name,
                    net_id=slot.peer_id,
                )
                spawn_requests.append(req)
        return spawn_requests

    # Draw JOIN browser ##########################################################################
    
    def _draw_join_browser(self, surface: Surface, lobby_state: LobbyState) -> None:
        hosts_comp: Optional[AvailableHosts] = None
        for _, comps in self.world.query(AvailableHosts):
            hosts_comp = comps[AvailableHosts]
            break

        surface.fill((10, 10, 18))

        title = self.font.render("Select a host to join:", True, (255, 255, 255))
        surface.blit(title, (20, 20))

        if hosts_comp is None or not hosts_comp.hosts:
            msg = self.font.render("(No hosts found yet)", True, (200, 200, 200))
            surface.blit(msg, (20, 60))
        else:
            y = 60
            for i, h in enumerate(hosts_comp.hosts):
                selected = (i == hosts_comp.selected_index)
                prefix = "> " if selected else "  "
                color = (255, 255, 255) if selected else (200, 200, 200)
                line = self.font.render(prefix + h, True, color)
                surface.blit(line, (40, y))
                y += 24

        hint = self.font.render("Enter: join   Esc: back", True, (255, 255, 255))
        surface.blit(hint, (20, Config.WINDOW_H - 32))
