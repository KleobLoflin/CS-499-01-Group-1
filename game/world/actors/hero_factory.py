# Hero Factory script used to generate hero entities (player characters)

from game.world.actors.blueprint import apply_blueprint
from game.world.actors.blueprint_index import hero as hero_bp
from game.world.components import Player

# links entitys with the intended components using blueprint functions
# from blueprint.py and blueprint_index.py
# returns the entity id representing the entity that was created and processed
def create(world, archetype: str, owner_client_id, pos) -> int:

    eid = world.new_entity()
    bp = hero_bp(f"hero.{archetype}")
    apply_blueprint(world, eid, bp, ctx={"pos": pos, "owner": owner_client_id})

    if owner_client_id is not None:
        world.add(eid, Player(owner_client_id))

    return eid