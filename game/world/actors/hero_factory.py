from game.world.components import Transform, Intent, DebugRect, MoveSpeed
from game.core.config import Config

def create(world, archetype: str, owner_client_id, pos) -> int:

    # build a player entity
    eid = world.new_entity()
    world.add(eid, Transform(x=pos[0], y=pos[1]))
    world.add(eid, Intent())
    world.add(eid, MoveSpeed(220))
    world.add(eid, DebugRect(size=Config.RECT_SIZE, color=Config.RECT_COLOR))
    
    return eid