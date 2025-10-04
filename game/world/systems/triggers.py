# game/world/systems/triggers.py

import pygame
from game.world.components import Transform, Map, OnMap

class TriggerSystem:
    def __init__(self, scene):
        self.scene = scene  # to call change_map()

    def update(self, world, dt):
        # Get the player Transform
        player_transform = world.get(self.scene.player_id, Transform)
        if not player_transform:
            print("[TriggerSystem] No player transform found")
            return

        # only process triggers if the player is on the active map 
        player_onmap = world.get(self.scene.player_id, OnMap)

        # Represent player as a rect for collision checking
        player_rect = pygame.Rect(player_transform.x, player_transform.y, 32, 32)  # adjust size

        # Find the active map
        active_map = None
        active_map_id = None
        for _, comps in world.query(Map):
            mp = comps[Map]
            if mp.active:
                active_map = mp.tmx_data
                active_map_id = getattr(mp, "id", None)
                break

        if not active_map:
            print("[TriggerSystem] No active map found")
            return

        # If player has an OnMap tag and it doesn't match the active map id, skip
        if player_onmap and active_map_id and player_onmap.id != active_map_id:
            return
        
        # Find the triggers layer
        trigger_layer = None
        for layer in active_map.objectgroups:
            if layer.name.lower() == "triggers":
                trigger_layer = layer
                break

        if not trigger_layer:
            # some maps may not have triggers
            print("[TriggerSystem] No layer named 'triggers'")
            return

        # Check each object in the triggers layer
        for obj in trigger_layer:
            trigger_type = obj.properties.get("trigger_type")
            if trigger_type != "exit":
                continue

            exit_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
            if player_rect.colliderect(exit_rect):

                # Map transition info
                target_map = obj.properties.get("target_map")

                if target_map:
                    # Use provided coordinates, or keep current player position
                    tx = int(float(obj.properties.get("target_x", 0)))
                    ty = int(float(obj.properties.get("target_y", 0)))
                    self.scene.change_map(target_map, tx, ty)
                    break
