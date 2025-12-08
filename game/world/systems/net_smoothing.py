# AUTHORED BY: Scott Petty

# used by client only
# moves Transform.x/.y towards Transform.net_x/.net_y each frame

from game.world.components import Transform

class NetSmoothingSystem:
    SMOOTH_SPEED = 15.0  # higher = snappier, lower = more floaty

    def update(self, world, dt: float) -> None:
        alpha = self.SMOOTH_SPEED * dt
        # Clamp alpha so it doesn't overshoot if dt spikes
        if alpha > 1.0:
            alpha = 1.0

        for _eid, comps in world.query(Transform):
            tr: Transform = comps[Transform]

            # If no network target yet, skip
            if tr.net_x is None or tr.net_y is None:
                continue
            
            # if enemy just spawned from snapshot at (0, 0), snap to correct position
            if tr.x < 1 and tr.y < 1:
                tr.x = tr.net_x
                tr.y = tr.net_y
            
            else:
                # exponential smoothing toward target
                tr.x += (tr.net_x - tr.x) * alpha
                tr.y += (tr.net_y - tr.y) * alpha
