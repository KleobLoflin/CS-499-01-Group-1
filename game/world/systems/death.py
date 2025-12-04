# EDITED BY: Scott Petty

from game.world.components import Transform, Life, lifeSpan, OnMap, ActiveMapId, PlayerTag

class death:
    def update(self, world, dt: float) -> None:
        # get map id's that have players on them
        logic_map_ids: set[str] = set()
        for _eid, comps in world.query(PlayerTag, OnMap):
            om: OnMap = comps[OnMap]
            if om.id:
                logic_map_ids.add(om.id)

        # if no players yet, use ActiveMapId
        if not logic_map_ids:
            active_id = None
            for _eid, comps in world.query(ActiveMapId):
                active_id = comps[ActiveMapId].id
                break
            if active_id:
                logic_map_ids.add(active_id)

        # collect entities to delete first
        to_delete = []

        # ---- HP-based death ----
        for entity_id, comps in world.query(Transform, Life):
            life_comp: Life = comps[Life]
            if life_comp.hp > 0:
                continue

            # if entity is on a map, only process if that map has a player
            if logic_map_ids:
                om = comps.get(OnMap)
                if om is not None and om.id not in logic_map_ids:
                    continue
            
            to_delete.append(entity_id)

        # ---- lifespan-based death ----
        for entity_id, comps in world.query(Transform, lifeSpan):
            if logic_map_ids:
                om = comps.get(OnMap)
                if om is not None and om.id not in logic_map_ids:
                    continue

            lifespan = comps[lifeSpan]
            lifespan.elapsed += dt
            if lifespan.elapsed >= lifespan.duration:
                to_delete.append(entity_id)

        # ---- delete safely after iteration ----
        for eid in to_delete:
            world.delete_entity(eid)