

from game.world.components import Transform, Life, lifeSpan, OnMap, ActiveMapId

class death:
    def update(self, world, dt: float) -> None:
        # get active map ID
        active_id = None
        for _, comps in world.query(ActiveMapId):
            active_id = comps[ActiveMapId].id
            break

        # collect entities to delete first
        to_delete = []

        # ---- HP-based death ----
        for entity_id, comps in world.query(Transform, Life):
            if active_id is not None:
                om = comps.get(OnMap)
                if om and om.id != active_id:
                    continue

            life = comps[Life]
            if life.hp <= 0:
                to_delete.append(entity_id)

        # ---- lifespan-based death ----
        for entity_id, comps in world.query(Transform, lifeSpan):
            if active_id is not None:
                om = comps.get(OnMap)
                if om and om.id != active_id:
                    continue

            lifespan = comps[lifeSpan]
            lifespan.elapsed += dt
            if lifespan.elapsed >= lifespan.duration:
                to_delete.append(entity_id)

        # ---- delete safely after iteration ----
        for eid in to_delete:
            world.delete_entity(eid)