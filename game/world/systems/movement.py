# class: MovementSystem

from game.world.components import Transform, Intent, Movement
from game.core.config import Config

class MovementSystem:
    def update(self, world, dt: float) -> None:

        # loops through all entities that have transform and Intent components
        # and adjusts the transform values according to intent and movespeed
        for _, components in world.query(Transform, Intent, Movement):
            tr: Transform = components[Transform]
            it: Intent = components[Intent]
            mv: Movement = components[Movement]

            # velocity = intent * speed
            # dt (delta time) normalizes the amount of pixel movement per time
            # meaning, no matter what fps you run the game at, the movement speed will be practically the same
            tr.x += it.move_x * mv.speed * dt 
            tr.y += it.move_y * mv.speed * dt

            # Dash applies high speed while active
            tr.x += it.dash_x * Config.DASH_SPEED * dt
            tr.y += it.dash_y * Config.DASH_SPEED * dt