# class: MovementSystem

from game.world.components import Transform, Intent, Movement, Facing, Attack, OnMap, ActiveMapId, PlayerTag
from game.core.config import Config

class MovementSystem:
    def update(self, world, dt: float) -> None:
        # determine which map ids currently have players on them
        logic_map_ids: set[str] = set()
        for _, comps in world.query(Transform, PlayerTag, OnMap):
            om = comps[OnMap]
            logic_map_ids.add(om.id)

        # If there are no PlayerTag entities yet
        if not logic_map_ids:
            for _, comps in world.query(ActiveMapId):
                logic_map_ids.add(comps[ActiveMapId].id)
                break
        
        # loops through all entities that have transform and Intent components
        # and adjusts the transform values according to intent and movespeed
        for _, components in world.query(Transform, Intent, Movement, Facing, Attack):

            # Only simulate entities that are on a map that has at least one player
            if logic_map_ids:
                om = components.get(OnMap)
                if om is not None and om.id not in logic_map_ids:
                    continue

            tr: Transform = components[Transform]
            it: Intent = components[Intent]
            mv: Movement = components[Movement]
            face: Facing = components[Facing]
            atk: Attack = components[Attack]

            # dash ##################################################################################
            # reset cooldown and duration if dash is flagged, we are not attacking, and the cooldown is done
            if it.dash and mv.dash_cooldown == 0.0 and not atk.active:
                mv.dash_cooldown = mv.dash_max_cooldown
                mv.dash_duration = mv.dash_max_duration
                it.dash = False

            # run dash cooldown
            if mv.dash_cooldown > 0.0:
                mv.dash_cooldown = max(0.0, mv.dash_cooldown - dt)
            
            if mv.dash_duration > 0.0:
                mv.dash_duration = max(0.0, mv.dash_duration - dt)

            # write to transform ##################################################################
            # when we are not attacking
            if not atk.active:
                
                # normalize diagonal movement
                if it.move_x and it.move_y:
                    inv = 0.70710678118
                    it.move_x *= inv; it.move_y *= inv

                # movement 
                if mv.dash_duration > 0.0:
                    # Dash applies high speed while active
                    tr.x += it.move_x * mv.dash_speed * dt
                    tr.y += it.move_y * mv.dash_speed * dt
                else:
                    tr.x += it.move_x * mv.speed * dt 
                    tr.y += it.move_y * mv.speed * dt

                # Facing ###########################################################
                face.direction = it.facing
                