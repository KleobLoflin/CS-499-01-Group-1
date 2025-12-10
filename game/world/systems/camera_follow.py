# AUTHORED BY: Scott Petty
# EDITED BY: COLE HERZOG

from game.world.components import (
    Camera,
    CameraFollowLocalPlayer,
    Transform,
    PlayerTag,
    LocalControlled,
    ActiveMapId,
    OnMap,
)


class CameraFollowSystem:
    def update(self, world, dt: float) -> None:

        # Get active map 
        active_id = None
        for _, comps in world.query(ActiveMapId):
            active_id = comps[ActiveMapId].id
            break
        
        # Find camera that follows local player
        cam_eid, cam = None, None
        for eid, comps in world.query(Camera, CameraFollowLocalPlayer):
            cam_eid, cam = eid, comps[Camera]
            break
        if cam is None:
            return

        
        # Choose the target entity:
        #   1) Prefer the local-controlled player on the active map
        #   2) If none, fall back to any player (spectate mode)
        target_tr = None
        target_eid = None

        # 1) Prefer the local-controlled player (normal behavior)
        for eid, comps in world.query(PlayerTag, LocalControlled, Transform):
            # make sure target is in active map
            if active_id is not None:
                om = comps.get(OnMap)
                if om is not None and om.id != active_id:
                    continue
            target_tr = comps[Transform]
            target_eid = eid
            break

        # 2) If local-controlled hero no longer exists (dead),
        #    fall back to *any* player so we can spectate others,
        #    ignoring ActiveMapId
        if target_tr is None:
            for eid, comps in world.query(PlayerTag, Transform):
                target_tr = comps[Transform]
                target_eid = eid
                break

        # No players
        if target_tr is None:
            cam.target_eid = None
            cam.spectate = False
            return

        # Remember who we’re following
        cam.target_eid = target_eid
        cam.spectate = (world.get(target_eid, LocalControlled) is None)

        # compute deadzone rectangle in world space
        hw, hh = cam.viewport_w // 2, cam.viewport_h // 2
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
        