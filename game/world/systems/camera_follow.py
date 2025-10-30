from game.world.components import (
    Camera, CameraFollowLocalPlayer, Transform, PlayerTag, 
    LocalControlled, ActiveMapId, OnMap
)

class CameraFollowSystem:
    def update(self, world, dt: float) -> None:

        # get active map
        active_id = None
        for _, comps in world.query(ActiveMapId):
            active_id = comps[ActiveMapId].id
            break

        # find camera that follows local player
        cam_eid, cam = None, None
        for eid, comps in world.query(Camera, CameraFollowLocalPlayer):
            cam_eid, cam = eid, comps[Camera]
            break
        if cam is None:
            return
        
        # choose the target
        target_tr = None
        for _, comps in world.query(PlayerTag, LocalControlled, Transform):
            # make sure target is in active map
            if active_id is not None:
                om = comps.get(OnMap)
                if om is not None and om.id != active_id:
                    continue
            target_tr = comps[Transform]
            break
        if target_tr is None:
            return
        
        # compute deadzone rectangle in world space
        hw, hh = cam.veiwport_w // 2, cam.veiwport_h // 2
        view_left = cam.x - hw
        view_top = cam.y - hh
        dz_left = view_left + (cam.viewport_w - cam.deadzone_w) // 2
        dz_top = view_top + (cam.viewport_h - cam.deadzone_h) // 2
        dz_right = dz_left + cam.deadzone_w
        dz_bottom = dz_top + cam.deadzone_h

        dx, dy = 0.0, 0.0

        if target_tr.x < dz_left: dx = target_tr.x - dz_left
        if target_tr.x > dz_right: dx = target_tr.x - dz_right
        if target_tr.y < dz_top: dy = target_tr.y - dz_top
        if target_tr.y > dz_bottom: dy = target_tr.y - dz_bottom

        # nudge camera towards target drift
        k = 12.0
        alpha = min(1.0, k * dt)
        cam.x += dx * alpha
        cam.y += dy * alpha

        if cam.pixel_snap:
            cam.x = float(int(cam.x))
            cam.y = float(int(cam.y))
        