# AUTHORED BY: Scott Petty

# sound system that runs in all scenes

from __future__ import annotations

from typing import Dict, List, Tuple

from game.world.components import (
    SoundRequest,
    Transform,
    LocalControlled,
    OnMap,
    TitleMenu,
    LobbyState,
)
from game.sound import audio


class SoundSystem:
    # How far away you can hear positional world sounds (pixels)
    HEARING_RADIUS: float = 512.0

    def update(self, world, dt: float) -> None:
        
        # scene music
        scene_kind = self._detect_scene_kind(world)
        audio.set_scene_music(scene_kind)

        # get local controlled player
        listeners: List[Tuple[float, float]] = []
        for _eid, comps in world.query(LocalControlled, Transform):
            tr: Transform = comps[Transform]
            listeners.append((float(tr.x), float(tr.y)))

        # find the map the the local controlled player is on
        local_maps: set[str] = set()
        for _eid, comps in world.query(LocalControlled, OnMap):
            om: OnMap = comps[OnMap]
            map_id = getattr(om, "id", None)
            if map_id:
                local_maps.add(map_id)

        hearing_radius_sq = self.HEARING_RADIUS * self.HEARING_RADIUS

        # enemy aggro sounds determined by size
        # big / medium / small / tiny
        enemy_aggro_by_size: Dict[str, List[SoundRequest]] = {}
        generic_requests: List[SoundRequest] = []

        # iterate through all SoundRequest comps
        for eid, comps in world.query(SoundRequest):
            req: SoundRequest = comps[SoundRequest]

            # Map gating 
            if not req.global_event and local_maps:
                onmap = comps.get(OnMap)
                if onmap is None or getattr(onmap, "id", None) not in local_maps:
                    # Not on a map we care about
                    del comps[SoundRequest]
                    continue

            # Distance gating
            if not req.global_event and listeners:
                tr = comps.get(Transform)
                if tr is not None:
                    sx, sy = float(tr.x), float(tr.y)
                    too_far = True
                    for lx, ly in listeners:
                        dx = sx - lx
                        dy = sy - ly
                        if dx * dx + dy * dy <= hearing_radius_sq:
                            too_far = False
                            break
                    if too_far:
                        del comps[SoundRequest]
                        continue

            # Classify enemy_aggro separately by size
            if req.event == "enemy_aggro":
                size = (req.subtype or "small").lower()
                if size not in ("big", "medium", "small", "tiny"):
                    size = "small"
                enemy_aggro_by_size.setdefault(size, []).append(req)
            else:
                generic_requests.append(req)

            # Consume the request so it won't be used next frame
            del comps[SoundRequest]

        # enemy aggro sounds
        for size, reqs in enemy_aggro_by_size.items():
            if not reqs:
                continue
            # If there were many, keep it to 2 per size
            reqs = reqs[:3]
            group_id = f"enemy.aggro.{size}"
            for _req in reqs:
                audio.play_sfx_group(group_id)

        # other sfx
        for req in generic_requests:
            self._handle_generic(req)

    # Scene detection for music ###############################################################
    
    def _detect_scene_kind(self, world) -> str:
        # check which scene we are in based on singletons
        # Title scene?
        for _eid, _comps in world.query(TitleMenu):
            return "title"

        # Hub / lobby scene?
        for _eid, _comps in world.query(LobbyState):
            return "hub"

        # Everything else Dungeon scene
        return "dungeon"

   
    # Generic SFX routing ####################################################################

    def _handle_generic(self, req: SoundRequest) -> None:
        event = req.event
        subtype = (req.subtype or "").lower()

        # UI / menu
        if event == "menu_move":
            audio.play_sfx_group("ui.menu_item_change")
        elif event == "menu_confirm":
            audio.play_sfx_group("ui.menu_item_change")
        elif event == "char_change":
            audio.play_sfx_group("ui.menu_item_change")
        elif event == "ready_up":
            audio.play_sfx_group("ui.ready_up")

        #  Player actions 
        elif event == "player_swing":
            audio.play_sfx_group("player.sword_swing")
        elif event == "player_dash":
            audio.play_sfx_group("player.dash")
        elif event == "player_hit":
            audio.play_sfx_group("misc.damage")
        elif event == "player_death":
            audio.play_sfx_group("enemy.death.medium")  # change later when player death is implemented

        # Enemy actions 
        elif event == "enemy_hit":
            audio.play_sfx_group("misc.damage")
        elif event == "enemy_death":
            size = subtype if subtype in ("big", "medium", "small", "tiny") else "small"
            audio.play_sfx_group(f"enemy.death.{size}")

        # Map transitions 
        elif event == "map_transition":
            audio.play_sfx_group("misc.transition")
        
        # object interactions

        elif event == "chest_open":
            audio.play_sfx_group("misc.chest_open")