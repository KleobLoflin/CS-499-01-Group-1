
from game.world.components import lifeSpan



    
class LifeSpanSystem:
    def update(self, world, dt: float) -> None:
       
        # collect entities that should die
        to_delete = []

        # tick down all lifespan timers
        for entity_id, comps in world.query(lifeSpan):
            ls = comps[lifeSpan]
            ls.duration -= dt

            # when time runs out, mark for deletion
            if ls.duration <= 0:
                to_delete.append(entity_id)

        # safely delete after iteration
        for eid in to_delete:
            world.delete_entity(eid)