from game.world.components import Camera

class CameraClampSystem:
    def update(self, world, dt: float) -> None:
        for _, comps in world.query(Camera):
            cam = comps[Camera]
            if cam.clamp_rect is None:
                continue
            
            x, y, w, h = cam.clamp_rect
            hw, hh = cam.viewport_w // 2, cam.viewport_h // 2
            min_x, max_x = x + hw, x + w - hw
            min_y, max_y = y + hh, y + h - hh

            # handle maps smaller than viewport
            if min_x > max_x:
                cam.x = (x + x + w) / 2
            else:
                cam.x = max(min_x, min(max_x, cam.x))
            if min_y > max_y:
                cam.y = (y + y + h) / 2
            else:
                cam.y = max(min_y, min(max_y, cam.y))
            
