from game.world.components import Transform, Intent, DebugRect, MoveSpeed, AI
from game.core.config import Config

def create(world, kind: str, pos, params=None) -> int:

    # build an enemy entity. "kind" can be used to pick the type of AI.
    params = params or {}
    eid = world.new_entity()
    world.add(eid, Transform(x=pos[0], y=pos[1]))
    world.add(eid, Intent())
    world.add(eid, MoveSpeed(params.get("speed", 200)))
    world.add(eid, AI(kind=kind, target_id=params.get("target_id", None)))
    world.add(eid, DebugRect(size=Config.RECT_SIZE, color=params.get("color", (255, 0, 0))))
    
    return eid