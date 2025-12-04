# AUTHORED BY: Scott Petty

from game.world.components import Camera, CameraFollowLocalPlayer, Transform
from game.world.components import PlayerTag, LocalControlled

class EnsureCameraSystem:
    def update(self, world, dt: float) -> None:
        # If a camera already exists, do nothing
        for _, _ in world.query(Camera):
            return

        # Find the local player to set initial camera position
        for _, comps in world.query(PlayerTag, LocalControlled, Transform):
            tr = comps[Transform]
            cam_eid = world.new_entity()
            world.add(cam_eid, Camera(x=tr.x, y=tr.y))
            world.add(cam_eid, CameraFollowLocalPlayer())
            return
