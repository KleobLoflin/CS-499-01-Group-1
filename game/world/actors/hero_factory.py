from game.world.actors.blueprint import apply_blueprint
from game.world.actors.blueprint_index import hero as hero_bp

def create(world, archetype: str, owner_client_id, pos) -> int:

    # build a player entity
    eid = world.new_entity()
    bp = hero_bp(f"hero.{archetype}")
    apply_blueprint(world, eid, bp, ctx={"pos": pos, "owner": owner_client_id})
    
    return eid