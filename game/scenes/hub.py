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
# NOTE: Real network I/O is intentionally left as TODO (net modules are empty in the zip).
#       All hooks are in place via NetIdentity / Owner / LobbySlot.peer_id / SpawnRequest.

from __future__ import annotations
from typing import List, Optional, Tuple

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
)
from game.world.actors.hero_factory import create as create_hero
from game.world.systems.animation import AnimationSystem
from game.world.systems.render import RenderSystem
from game.world.systems.hub_preview import HubPreviewSystem
from game.world.maps.map_index import load_registry
from game.world.maps.map_factory import create_or_activate, resolve_map_hint_to_id


class HubScene(Scene):
    """
    mode: "SINGLE", "HOST", or "JOIN"
    """

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

        # minimal systems: just animation; rendering is called manually
        self.world.systems = [
            HubPreviewSystem(),
            AnimationSystem(),
        ]
        self.render_system = RenderSystem()

        # basic font for overlay UI
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 16)

        # Net identity for this process
        if self.mode == "SINGLE":
            self.peer_id = "solo"
            self.role = "SOLO"
        elif self.mode == "HOST":
            self.peer_id = "host"
            self.role = "HOST"
        else:
            self.peer_id = "client"
            self.role = "CLIENT"

    # -------------------------------------------------------------------------
    # Scene life cycle
    # -------------------------------------------------------------------------

    def enter(self) -> None:
        # 1) Load hub map as background
        load_registry("data/map_registry.json")
        hub_id = resolve_map_hint_to_id("hub") or "hub"
        create_or_activate(self.world, hub_id)

        # 2) Create NetIdentity singleton
        e_net = self.world.new_entity()
        self.world.add(e_net, NetIdentity(my_peer_id=self.peer_id, role=self.role))

        # 3) Create LobbyState singleton
        lobby_e = self.world.new_entity()
        substate = "BROWSER" if self.mode == "JOIN" else "SELECT"
        lobby_state = LobbyState(
            mode=self.mode,
            substate=substate,
            character_catalog=[f"hero.{name}" for name in self.HERO_CATALOG],
        )
        self.world.add(lobby_e, lobby_state)

        # 4) AvailableHosts singleton (JOIN only)
        if self.mode == "JOIN":
            self.world.add(lobby_e, AvailableHosts())

        # 5) Create up to 5 LobbySlot entities
        # Slot assignment policy:
        #   SINGLE: slot 0 is local.
        #   HOST:   slot 0 is local host; others wait for remote peers.
        #   JOIN:   no local slot yet; becomes available when we "join" a host lobby.
        for i in range(5):
            is_local = (self.mode in ("SINGLE", "HOST") and i == 0)
            peer_id = self.peer_id if is_local else None
            name = "You" if is_local else f"Player {i + 1}"

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

        # (Networking TODO) In HOST mode, you would start listening here.
        # (Networking TODO) In JOIN mode, you would kick off host discovery here.

    def exit(self) -> None:
        # nothing special yet
        pass

    # -------------------------------------------------------------------------
    # Event handling (keyboard)
    # -------------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            # Let the App handle quitting – nothing special here.
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
        # Drive ECS animation
        self.world.update(dt)

        # Update previews if anyone changed selection, etc. (no-op most frames)
        self._sync_previews()

        # In HOST / SINGLE, check ready state and transition to DungeonScene
        lobby_state = self._get_lobby_state()
        if lobby_state and lobby_state.substate == "SELECT":
            if self._should_transition_to_dungeon(lobby_state):
                spawn_requests = self._build_spawn_requests()
                if spawn_requests:
                    # Role: SOLO / HOST / CLIENT changed by menu → here we map:
                    if self.mode == "SINGLE":
                        role = "SOLO"
                    elif self.mode == "HOST":
                        role = "HOST"
                    else:
                        role = "CLIENT"

                    next_scene = DungeonScene(role=role, spawn_requests=spawn_requests)
                    self.scene_manager.set(next_scene)

    def draw(self, surface: Surface) -> None:
         # 1) Draw the tiled hub map + any world entities (hero previews)
        self.render_system.draw(self.world, surface)
        
        # 2) Draw lobby overlay UI
        lobby_state = self._get_lobby_state()
        if lobby_state is None:
            return

        if self.mode == "JOIN" and lobby_state.substate == "BROWSER":
            self._draw_join_browser(surface, lobby_state)
        else:
            self._draw_lobby_overlay(surface, lobby_state)

    # -------------------------------------------------------------------------
    # Helpers: Lobby / slots
    # -------------------------------------------------------------------------

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

    # --- key handling for JOIN browser --------------------------------------

    def _handle_join_browser_key(self, lobby_state: LobbyState, key: int) -> None:
        # NOTE: This is a pure stub – replace host list handling with real net code.
        # For now we just have a fake single host entry called "Local Host".
        hosts_comp: Optional[AvailableHosts] = None
        for _, comps in self.world.query(AvailableHosts):
            hosts_comp = comps[AvailableHosts]
            break

        if hosts_comp is None:
            return

        if not hosts_comp.hosts:
            hosts_comp.hosts.append("Local Host (debug)")

        if key in (pygame.K_UP, pygame.K_w):
            hosts_comp.selected_index = max(0, hosts_comp.selected_index - 1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            hosts_comp.selected_index = min(
                len(hosts_comp.hosts) - 1, hosts_comp.selected_index + 1
            )
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            # Pretend we successfully joined the selected host's lobby.
            # Networking TODO: handshake, receive authoritative lobby snapshot, etc.
            lobby_state.substate = "SELECT"
            self._configure_joined_slots_for_debug()

    def _configure_joined_slots_for_debug(self) -> None:
        """
        Debug-only helper: after "joining" a host, we fabricate a lobby with:
            slot 0: host (not local)
            slot 1: this client (local)
        Other slots empty.
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

    # --- key handling for SELECT (actual 5-column lobby UI) -----------------

    def _handle_lobby_select_key(self, lobby_state: LobbyState, key: int) -> None:
        local = self._find_local_slot()
        if local is None:
            return
        slot_eid, slot = local

        catalog_len = len(self.HERO_CATALOG)

        if key in (pygame.K_UP, pygame.K_w):
            slot.selected_char_index = (slot.selected_char_index - 1) % catalog_len
            slot.ready = False
            self._refresh_slot_preview(slot_eid, slot)
        elif key in (pygame.K_DOWN, pygame.K_s):
            slot.selected_char_index = (slot.selected_char_index + 1) % catalog_len
            slot.ready = False
            self._refresh_slot_preview(slot_eid, slot)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            slot.ready = not slot.ready
        # Host-only shortcut: R key toggles all non-empty slots to ready (debug)
        elif key == pygame.K_r and self.mode == "HOST":
            for _, s in self._iter_slots():
                if s.peer_id is not None:
                    s.ready = True

    # --- preview hero entities ----------------------------------------------

    def _slot_preview_position(self, index: int) -> Tuple[float, float]:
        # Evenly spaced columns across the window, center vertically.
        # index ∈ [0, 4]
        columns = 5
        x = (Config.WINDOW_W / (columns + 1)) * (index + 1)
        y = Config.WINDOW_H / 2
        return x, y

    def _refresh_slot_preview(self, slot_eid: int, slot: LobbySlot) -> None:
        # Delete existing preview if any
        if slot.preview_eid is not None:
            self.world.delete_entity(slot.preview_eid)
            slot.preview_eid = None

    def _sync_previews(self) -> None:
        # Currently a no-op. Left here incase we want to set/check some kind of flags later
        return

    # --- ready check / spawn requests ---------------------------------------

    def _should_transition_to_dungeon(self, lobby_state: LobbyState) -> bool:
        if self.mode == "SINGLE":
            # Only the local slot matters
            local = self._find_local_slot()
            return bool(local and local[1].ready)

        # HOST / JOIN: all occupied slots must be ready, and at least one occupied
        any_occupied = False
        for _, slot in self._iter_slots():
            if slot.peer_id is not None:
                any_occupied = True
                if not slot.ready:
                    return False
        return any_occupied

    def _build_spawn_requests(self) -> List[SpawnRequest]:
        spawn_requests: List[SpawnRequest] = []
        for _, slot in self._iter_slots():
            if slot.ready and (slot.peer_id is not None or slot.is_local):
                hero_name = self.HERO_CATALOG[slot.selected_char_index]
                hero_key = f"hero.{hero_name}"
                req = SpawnRequest(
                    hero_key=hero_key,
                    is_local=slot.is_local,
                    player_name=slot.name,
                    net_id=slot.peer_id,
                )
                spawn_requests.append(req)
        return spawn_requests

    # -------------------------------------------------------------------------
    # Drawing overlay: 5 columns + labels / ready state
    # -------------------------------------------------------------------------

    def _draw_lobby_overlay(self, surface: Surface, lobby_state: LobbyState) -> None:
        # Column rectangles + text
        padding = 8
        col_width = Config.WINDOW_W // 5
        top = 20
        bottom = Config.WINDOW_H - 40

        for _, slot in self._iter_slots():
            left = slot.index * col_width
            rect = pygame.Rect(left + padding, top, col_width - 2 * padding, bottom - top)

            # BG color based on slot state
            if slot.peer_id is None and not slot.is_local:
                color = (40, 40, 50)  # waiting
            elif slot.ready:
                color = (40, 80, 40)  # ready
            else:
                color = (80, 80, 40)  # active but not ready

            pygame.draw.rect(surface, color, rect, border_radius=8)
            pygame.draw.rect(surface, (200, 200, 220), rect, width=2, border_radius=8)

            # Slot label
            title = slot.name
            label = self.font.render(title, True, (255, 255, 255))
            surface.blit(label, (rect.x + 6, rect.y + 4))

            # Character name
            hero_name = self.HERO_CATALOG[slot.selected_char_index]
            char_text = f"{hero_name.replace('_', ' ').title()}"
            char_surf = self.font.render(char_text, True, (230, 230, 230))
            surface.blit(char_surf, (rect.x + 6, rect.y + 26))

            # Status text
            if slot.peer_id is None and not slot.is_local:
                status = "Waiting for player"
            elif slot.ready:
                status = "READY"
            else:
                status = "Press Enter to ready"

            status_surf = self.font.render(status, True, (230, 230, 230))
            surface.blit(status_surf, (rect.x + 6, rect.bottom - 24))

        # Footer instructions
        footer = ""
        if self.mode == "SINGLE":
            footer = "↑/↓: choose hero   Enter/Space: ready   Esc: back"
        elif self.mode == "HOST":
            footer = "↑/↓: choose hero   Enter/Space: ready   R: ready all (debug)   Esc: back"
        else:
            footer = "↑/↓: choose hero   Enter/Space: ready   Esc: back"

        footer_surf = self.font.render(footer, True, (255, 255, 255))
        surface.blit(footer_surf, (16, Config.WINDOW_H - 24))

    def _draw_join_browser(self, surface: Surface, lobby_state: LobbyState) -> None:
        hosts_comp: Optional[AvailableHosts] = None
        for _, comps in self.world.query(AvailableHosts):
            hosts_comp = comps[AvailableHosts]
            break

        surface.fill((10, 10, 18))

        title = self.font.render("Searching for hosts...", True, (255, 255, 255))
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

        hint = self.font.render("↑/↓: select host   Enter: join   Esc: back", True, (255, 255, 255))
        surface.blit(hint, (20, Config.WINDOW_H - 32))
