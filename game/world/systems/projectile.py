# AUTHORED BY: Nicholas Loflin


from game.world.components import (Transform, Intent, OnMap, ProjectileRequest)
from game.world.actors.enemy_factory import create as create_enemy


class ProjectileSpawnSystem:

    
    def update(self, world, dt):
        to_remove = []

       
        for eid, comps in list(world.query(ProjectileRequest, Transform, OnMap)):
            shoot = comps[ProjectileRequest]
            tr = comps[Transform]
            onmap = comps[OnMap]
            req: ProjectileRequest = comps[ProjectileRequest]
            
            proj_id = create_enemy(
                world,
                kind= req.spawn_kind,
                pos=(tr.x, tr.y),
                params={"owner": eid}
            )

            world.add(proj_id, OnMap(id=onmap.id))

            # aim
            intent = world.get(proj_id, Intent)
            if intent is None:
                intent = Intent()
                world.add(proj_id, intent)

            dx = shoot.target_pos[0] - tr.x
            dy = shoot.target_pos[1] - tr.y
            dist = max((dx*dx + dy*dy)**0.5, 0.001)

            intent.move_x = dx / dist
            intent.move_y = dy / dist

            

            # CONSUME EVENT
            del world.entities[eid][ProjectileRequest]

            #to_remove.append(eid)

        # cleanup requests
        #for eid in to_remove:
            #if world.get(eid, ProjectileRequest):
                #world.remove(eid, ProjectileRequest)