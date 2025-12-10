#WORKED ON BY: Colin Adams, Scott Petty
# game/world/systems/triggers.py
#Performs actions based on invisble rectangles in the map
import pygame
from game.world.components import Transform, Map, OnMap, PlayerTag, SoundRequest, Life

class TriggerSystem:
    def __init__(self, scene):
        self.scene = scene  # to call change_map()

    def update(self, world, dt):
        # check exit triggers for all players, per map
        # build index of map_id -> TMX object triggers layer
        triggers_by_map_id: dict[str, object] = {}
        for _eid, comps in world.query(Map):
            mp: Map = comps[Map]
            map_id = getattr(mp, "id", None)
            tmx = getattr(mp, "tmx_data", None)
            if not map_id or not tmx:
                continue

            # Find the triggers layer once per map
            trigger_layer = None
            for layer in tmx.objectgroups:
                if not getattr(layer, "name", None):
                    continue
                if layer.name.lower() == "triggers":
                    trigger_layer = layer
                    break

            if trigger_layer is not None:
                triggers_by_map_id[map_id] = trigger_layer

        if not triggers_by_map_id:
            return

        # gather all transitions
        pending_transitions: list[tuple[int, str, float, float]] = []

        # get all players
        players = list(world.query(PlayerTag, Transform, OnMap))


        # For each player, only check triggers on the same map
        for pid, comps in players:
            tr: Transform = comps[Transform]
            onmap: OnMap = comps[OnMap]
            map_id = getattr(onmap, "id", None)
            if not map_id:
                continue

            trigger_layer = triggers_by_map_id.get(map_id)
            if trigger_layer is None:
                continue

            # player rect for collision checking
            player_rect = pygame.Rect(tr.x, tr.y, 16, 16)  # TODO: tie to hitbox/sprite size

            for obj in trigger_layer:
                trigger_type = obj.properties.get("trigger_type")
                if isinstance(trigger_type, str):
                    trigger_type = trigger_type.lower()

                if trigger_type != "exit":
                    continue

                exit_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                if not player_rect.colliderect(exit_rect):
                    continue
                
                target_map = obj.properties.get("target_map")
                if not target_map:
                    continue

                # If target_x/target_y are omitted, keep current position
                tx = obj.properties.get("target_x")
                ty = obj.properties.get("target_y")
                if tx is None:
                    tx = tr.x
                else:
                    tx = float(tx)

                if ty is None:
                    ty = tr.y
                else:
                    ty = float(ty)

                # record the transition
                pending_transitions.append((pid, target_map, tx, ty))

                # sound request for map transition
                comps_pid = world.components_of(pid)
                comps_pid[SoundRequest] = SoundRequest(
                    event="map_transition",   
                    global_event=False,       
                )

                # player heal 1 hp everytime that get to a new map
                life: Life = comps[Life]
                if life.hp <= 4:
                    life.hp += 2
                elif life.hp == 5:
                    life.hp += 1

                # Don't process multiple exits for the same player in a single frame
                break

        # Delegate actual transition to the scene, per-entity.
        for pid, target_map, tx, ty in pending_transitions:
            if hasattr(self.scene, "change_map_for_entity"):
                self.scene.change_map_for_entity(pid, target_map, tx, ty)
            else:
                if getattr(self.scene, "player_id", None) == pid and hasattr(self.scene, "change_map"):
                    self.scene.change_map(target_map, tx, ty)