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

            # exponential smoothing toward target
            tr.x += (tr.net_x - tr.x) * alpha
            tr.y += (tr.net_y - tr.y) * alpha
