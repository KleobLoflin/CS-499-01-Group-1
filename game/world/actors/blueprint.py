# contains builder functions that instantiate components based on
# data from .json files

# Any addition or deletion of components in components.py needs to be reflected
# in these component builder functions

from game.world.components import *

def build_PlayerTag(spec, ctx): return PlayerTag()

def build_Transform(spec, ctx):
    x, y = ctx.get("pos", (0,0))
    return Transform(spec.get("x", x), spec.get("y", y))

def build_Intent(spec, ctx): return Intent()

def build_InputState(spec, ctx): return InputState()

def build_Movement(spec, ctx):
    return Movement(speed=float(spec.get("speed", 80)))

def build_AI(spec, ctx):
    return AI(kind=spec.get("kind", "wander"), target_id=ctx.get("target_id"), agro_range=spec.get("agro_range", 0))#,max_cooldown =spec.get("max_cooldown", 1.0))

def build_Sprite(spec, ctx):
    return Sprite(atlas_id=spec["atlas"], z=int(spec.get("z", 10)))

def build_AnimationState(spec, ctx):
    return AnimationState(clip=spec.get("clip", "idle"),
                          frame=0, time=0.0,
                          fps=float(spec.get("fps", 0.0)),
                          loop=bool(spec.get("loop", True)),
                          changed=True)

def build_Facing(spec, ctx): return Facing()

def build_DebugRect(spec, ctx):
    return DebugRect(size=tuple(spec.get("size", (16, 16))), color=tuple(spec.get("color", (90, 180, 255))))

def build_Attack(spec, ctx): return Attack(max_cooldown=spec.get("max_cooldown", 0.15))

def build_HitboxSize(spec, ctx):
    return HitboxSize(radius=spec.get("radius", 10))


def build_lifeSpan(spec, ctx):
    return lifeSpan(duration=spec.get("duration", 5))


# gather all builder functions
BUILDERS = {
    "PlayerTag": build_PlayerTag,
    "Transform": build_Transform,
    "Intent": build_Intent,
    "InputState": build_InputState,
    "Movement": build_Movement,
    "AI": build_AI,
    "Sprite": build_Sprite,
    "AnimationState": build_AnimationState,
    "Facing": build_Facing,
    "Attack": build_Attack,
    "DebugRect": build_DebugRect,
    "HitboxSize": build_HitboxSize,
    "lifeSpan": build_lifeSpan
}

# uses builder functions to add components to an entity
# gets the appropriate components depending on entity id and calls
# world.add() to link them.
def apply_blueprint(world, eid, blueprint: dict, ctx: dict):
    for spec in blueprint.get("components", []):
        t = spec["type"]
        comp = BUILDERS[t](spec, ctx)
        world.add(eid, comp)