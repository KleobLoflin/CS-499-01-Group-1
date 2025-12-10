# AUTHORED BY: Scott Petty

from typing import Optional

from game.world.components import Camera, CameraFollowLocalPlayer, ActiveMapId, OnMap
from game.world.maps.map_factory import create_or_activate, resolve_map_hint_to_id


class ViewpointActiveMapSystem:
    def update(self, world, dt: float) -> None:
        # Find the camera that follows the local player / viewpoint
        cam = None
        for _eid, comps in world.query(Camera, CameraFollowLocalPlayer):
            cam = comps[Camera]
            break

        if cam is None:
            return

        target_eid = getattr(cam, "target_eid", None)
        if target_eid is None:
            return

        # Look up that entity's OnMap
        om: OnMap | None = world.get(target_eid, OnMap)
        if om is None or not getattr(om, "id", None):
            return

        target_map_id: str = om.id

        # Current ActiveMapId (if any)
        current_id: Optional[str] = None
        for _eid, comps in world.query(ActiveMapId):
            current_id = comps[ActiveMapId].id
            break

        # Already on that map → nothing to do
        if current_id == target_map_id:
            return

        # Resolve any legacy TMX hints
        resolved_id = resolve_map_hint_to_id(target_map_id) or target_map_id

        # Delegate to map_factory to:
        #   - ensure a Map entity exists
        #   - toggle Map.active flags
        #   - set ActiveMapId
        create_or_activate(world, resolved_id)