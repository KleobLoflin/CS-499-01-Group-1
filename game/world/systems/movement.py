# class: MovementSystem

from game.world.components import Transform, Intent
from game.core.config import Config

class MovementSystem:
    def update(self, world, dt: float) -> None:

        # loops through all entities that have transform and Intent components
        # and adjusts the transform values according to intent and movespeed
        for _, components in world.query(Transform, Intent):
            tr: Transform = components[Transform]
            it: Intent = components[Intent]

            # velocity = intent * speed
            # dt (delta time) normalizes the amount of pixel movement per time
            # meaning, no matter what fps you run the game at, the movement speed will be practically the same
            tr.x += it.move_x * Config.MOVE_SPEED * dt 
            tr.y += it.move_y * Config.MOVE_SPEED * dt
            tr.x += it.dash_x * Config.DASH_LENGTH * dt
            tr.y += it.dash_y * Config.DASH_LENGTH * dt
