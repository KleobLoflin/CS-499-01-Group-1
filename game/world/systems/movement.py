# class: MovementSystem

from game.world.components import Transform, Intent, MoveSpeed
from game.core.config import Config

class MovementSystem:
    def update(self, world, dt: float) -> None:

        # loops through all entities that have transform and Intent components
        # and adjusts the transform values according to intent and movespeed
        for _, components in world.query(Transform, Intent, MoveSpeed):
            tr: Transform = components[Transform]
            it: Intent = components[Intent]
            mv: MoveSpeed = components[MoveSpeed]

            # velocity = intent * speed
            # dt (delta time) normalizes the amount of pixel movement per time
            # meaning, no matter what fps you run the game at, the movement speed will be practically the same
            tr.x += it.move_x * mv.x * dt 
            tr.y += it.move_y * mv.x * dt
