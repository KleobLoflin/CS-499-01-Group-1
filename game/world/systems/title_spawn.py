import random
from typing import Dict, Any, Tuple, List
from game.world.spawn_components import MapLoaded
from game.world.actors.enemy_factory import create as create_enemy
from game.world.components import Intent, Movement, Facing

class TitleSpawnSystem:
    def __init__(self, area: Tuple[int, int, int, int]=(64, 64, 512, 256)):
        self.area = area
        self.did = False

    def update(self, world, dt: float):
        if self.did:
            return
        
        for _, comps in world.query(MapLoaded):
            ml: MapLoaded = comps[MapLoaded]
            self.spawn_from_blueprint(world, ml.blueprint)
            self.did = True
            break
    
    def spawn_from_blueprint(self, world, bp: Dict[str, Any]) -> None:
        entries: List[Dict[str, Any]] = bp.get("title_spawns") or []
        
        for entry in entries:
            if entry.get("kind") != "enemy":
                continue
            enemy_type = entry.get("enemy_type", "chort")
            count = int(entry.get("count", 1))
            points = entry.get("points") or []
            region = entry.get("region")

            for i in range(count):
                if i < len(points):
                    pos = tuple(points[i])
                else:
                    pos = self.sample_region(region) if region else self.rand_pos()
                eid = create_enemy(world, kind=enemy_type, pos=pos)
                
    def rand_pos(self) -> Tuple[int, int]:
        x0, y0, x1, y1 = self.area
        return random.randint(x0, x1), random.randint(y0, y1)
    
    def sample_region(self, region_name: str) -> Tuple[int, int]:
        # read bp["regions"][region_name] and sample inside shapes
        # ...
        # ...
        return self.rand_pos()
