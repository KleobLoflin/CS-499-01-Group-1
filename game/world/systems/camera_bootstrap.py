# AUTHORED BY: Scott Petty

# game/world/systems/camera_bootstrap.py
from game.world.components import Camera, ActiveMapId, Map
from game.world.maps.utils import map_world_bounds

class CameraBootstrapSystem:
    def update(self, world, dt: float) -> None:
        active_id = None
        for _, comps in world.query(ActiveMapId):
            active_id = comps[ActiveMapId].id
            break
        if active_id is None:
            return

        tmx = None
        for _, comps in world.query(Map):
            mp = comps[Map]
            if getattr(mp, "id", None) == active_id:
                tmx = getattr(mp, "tmx_data", None)
                break
        if tmx is None:
            return

        bounds = map_world_bounds(tmx)
        for _, comps in world.query(Camera):
            cam = comps[Camera]
            if cam.clamp_rect != bounds:
                cam.clamp_rect = bounds
