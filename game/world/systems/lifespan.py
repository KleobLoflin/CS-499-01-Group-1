
from game.world.components import lifeSpan


class LifeSpanSystem:#System):
    
    def update(self, world, dt: float) -> None:
        for entity, (lifespan,) in world.get_components(lifeSpan):
            lifespan.duration -= dt
            if lifespan.duration <= 0:
                world.delete_entity(entity)