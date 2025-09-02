from game.world.components import Transform, Intent
from game.core.config import Config

class MovementSystem:
    """Applies Intent to Transform at constant speed (no collisions yet)."""
    def update(self, world, dt: float) -> None:
        for _, comps in world.query(Transform, Intent):
            tr: Transform = comps[Transform]
            it: Intent = comps[Intent]
            tr.x += it.move_x * Config.MOVE_SPEED * dt
            tr.y += it.move_y * Config.MOVE_SPEED * dt
