

from game.world.components import Transform, Life, AI, lifeSpan, OnMap, ActiveMapId

class death:



     def update(self, world, dt: float) -> None:
        
        # get active map ID
        active_id = None
        for _, comps in world.query(ActiveMapId):
             active_id = comps[ActiveMapId].id
             break

        # drive AI for entities with AI + Transform + Intent
        for entity_id, comps in world.query(Transform, Life, AI): 
            # only move entities that are on the map
            if active_id is not None:
                om = comps.get(OnMap)
                if om is None or om.id != active_id:
                    continue

            ai: AI = comps[AI]
            life: Life = comps[Life]
            lifespan: lifeSpan =comps[lifeSpan]
        
            if life.hp <= 0: #or lifespan <=0:
                world.delete_entity(entity_id)
                




