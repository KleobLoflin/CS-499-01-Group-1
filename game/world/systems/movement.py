# class: MovementSystem

from game.world.components import Transform, Intent, MoveSpeed
from game.core.config import Config

class MovementSystem:
    def update(self, world, dt: float) -> None:
        for _, components in world.query(Transform, Intent):
            tr: Transform = components[Transform]
            it: Intent = components[Intent]

            # Normal walk
            tr.x += it.move_x * Config.MOVE_SPEED * dt 
            tr.y += it.move_y * Config.MOVE_SPEED * dt

            # Dash applies high speed while active
            tr.x += it.dash_x * Config.DASH_SPEED * dt
            tr.y += it.dash_y * Config.DASH_SPEED * dt
