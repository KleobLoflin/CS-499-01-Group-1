# reads blueprint["game_spans"] once after MapLoaded and spawns:
# - player at player_start.pos
# - pickups list
# - static_enemies list

# later expand to handle "waves" and trigger logic

from typing import Dict, Any, List, Tuple
from game.world.spawn_components import MapLoaded
from game.world.actors.enemy_factory import create as create_enemy
from game.world.actors.hero_factory import create as create_hero
from game.world.components import Intent, Movement, Facing

class GameplaySpawnSystem:
    def __init__(self):
        self.did_initial_spawns = False
    
    def update(self, world, dt: float):
        if self.did_initial_spawns:
            return
        
        for _, comps in world.query(MapLoaded):
            ml: MapLoaded = comps[MapLoaded]
            bp = ml.blueprint or []
            gs = bp.get("game_spawns") or {}
            if not gs:
                self.did_initial_spawns = True
                return
            
            # player spawn  (need to figure out how to handle a variable number of player spawns multiplayer)
            ps = gs.get("player_start")
            if ps and "pos" in ps:
                px, py = ps["pos"]
                player_id = create_hero(world, archetype="knight", owner_client_id=None, pos=(px, py))

            # pickups
            for p in gs.get("pickups", []):
                # ex: {"type":"potion_small", "pos":[x,y]}
                # TODO: write pickup factory soon
                pass

            # static enemies
            for e in gs.get("static_enemies", []):
                etype = e.get("type", "chort")
                ex, ey = e.get("pos", [0, 0])
                eid = create_enemy(world, kind=etype, pos=(ex, ey))
            
            self.did_initial_spawns = True
            break