# AUTHORED BY: Scott Petty
# Enemy Factory script used to generate enemy entities

from game.world.actors.blueprint import apply_blueprint
from game.world.actors.blueprint_index import enemy as enemy_bp

# links entitys with the intended components using blueprint functions
# from blueprint.py and blueprint_index.py
# returns the entity id representing the entity that was created and processed
def create(world, kind: str, pos, params=None) -> int:

    params = params or {}
    eid = world.new_entity()
    bp = enemy_bp(f"enemy.{kind}")
    ctx = {"pos": pos, "target_id": params.get("target_id")}
    apply_blueprint(world, eid, bp, ctx=ctx)
    return eid