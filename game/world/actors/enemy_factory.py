from game.world.actors.blueprint import apply_blueprint
from game.world.actors.blueprint_index import enemy as enemy_bp

def create(world, kind: str, pos, params=None) -> int:

    # build an enemy entity. 
    params = params or {}
    eid = world.new_entity()
    bp = enemy_bp(f"enemy.{kind}")
    ctx = {"pos": pos, "target_id": params.get("target_id")}
    apply_blueprint(world, eid, bp, ctx=ctx)
    return eid