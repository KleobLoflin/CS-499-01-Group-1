# AUTHORED BY: Nicholas Loflin
# EDITED BY: Scott Petty

# ai for the entities
# game/world/systems/ai.py


#this is the code to summon the ai specifically chaser

        #Spawn chort enemy entity with components that it will use
        #self.chaser_1_id = create_enemy(self.world, kind="chort", pos=(100, 100), params={"target_id" : self.player_id})

import random
import time
from game.world.actors.enemy_factory import create as create_enemy
from game.world.components import Transform, Intent, AI, PlayerTag, OnMap, SoundRequest, ActiveMapId, Attack, ProjectileRequest, ProjectileSpawner
from game.world.actors.blueprint import apply_blueprint
from game.world.actors.blueprint_index import enemy as enemy_bp
from game.sound.enemy_sound_utils import infer_enemy_size

# Moved AI dataclasses to components and now there is a "kind" label for the different kinds of AI.
# I filtered each code block for ai.kind so that it only runs if the kind of AI matches.
# you can add code blocks for as many AI kinds as you want and just filter for the ai.kind string of choice.
# I also removed the target.id check for wonder ai because it doesnt target a player
# -Scott


class EnemyAISystem:#System):
    
    def update(self, world, dt: float) -> None:
        # build a mapping of map_id -> list of player Transforms on that map
        players_by_map: dict[str, list[tuple[int, Transform]]] = {}
        for player_eid, comps in world.query(Transform, PlayerTag, OnMap):
            tr: Transform = comps[Transform]
            om: OnMap = comps[OnMap]
            players_by_map.setdefault(om.id, []).append((player_eid, tr))

        # drive AI for entities with AI + Transform + Intent
        for entity_id, comps in world.query(Transform, Intent, AI): 
            ai: AI = comps[AI]
            pos: Transform = comps[Transform]
            intent: Intent = comps[Intent]

            # get enemy size
            size = infer_enemy_size(ai)

            # pick nearest player on the same map as this AI
            target_pos: Transform | None = None

            if target_pos is None:
                ai_onmap = world.get(entity_id, OnMap)
                if ai_onmap is not None:
                    same_map_players = players_by_map.get(ai_onmap.id, [])
                    if same_map_players:
                        best_tr: Transform | None = None
                        best_dist2 = float("inf")
                        best_target_id: int | None = None
                        for p_eid, p_tr in same_map_players:
                            dx = p_tr.x - pos.x
                            dy = p_tr.y - pos.y
                            d2 = dx * dx + dy * dy
                            if d2 < best_dist2:
                                best_dist2 = d2
                                best_tr = p_tr
                                best_target_id = p_eid

                        target_pos = best_tr

                        # track which player this enemy is targeting
                        if best_target_id is not None:
                            ai.target_id = best_target_id

            # compute distance to target
            dx = 0.0
            dy = 0.0
            dist = float("inf")
            if target_pos != None:
                dx = target_pos.x - pos.x
                dy = target_pos.y - pos.y
                dist = (dx * dx + dy * dy) ** 0.5

            if dist > ai.agro_range or target_pos == None:
                # out of aggro range or no valid target so clear target_id
                ai.target_id = None

                # Give each AI its own cooldown + direction if not already present
                if not hasattr(ai, "wander_timer"):
                    ai.wander_timer = 0.0
                if not hasattr(ai, "wander_dir"):
                    ai.wander_dir = (0.0, 0.0)
                if not hasattr(ai, "wander_waiting"):
                    ai.wander_waiting = False

                ai.wander_timer -= dt
                if ai.wander_waiting:
                    if ai.wander_timer <= 0:

                        ai.wander_waiting = False
                        dx = random.randint(-10, 10)
                        dy = random.randint(-10, 10)
                        mag = max((dx * dx + dy * dy) ** 0.5, 1.0)
                        ai.wander_dir = (dx / mag, dy / mag)
                        ai.wander_timer = 1.0  # pick new direction every 1 second

                    # waiting
                    intent.move_x = 0.0
                    intent.move_y = 0.0
                else:
                    if ai.wander_timer <= 0:
                        ai.wander_waiting = True
                        ai.wander_timer = random.uniform(3.0,4.0)  # wait between 1-3 seconds
                        intent.move_x = 0.0
                        intent.move_y = 0.0
                    else:
                        # keep moving in that direction
                        intent.move_x = ai.wander_dir[0]
                        intent.move_y = ai.wander_dir[1]

            else:
                # only handle chase entities
                if ai.kind == "chase":
                    # check if in range
                    chasing_now = (dist > 10 and dist < ai.agro_range and target_pos is not None)

                    # previous chasing state
                    was_chasing = getattr(ai, "was_chasing", False)
                    ai.was_chasing = chasing_now

                    current_target_id = getattr(ai, "target_id", None)
                    last_sound_target_id = getattr(ai, "last_aggro_target_id", None)

                    if chasing_now:
                        intent.move_x = dx / dist
                        intent.move_y = dy / dist

                        # decide if aggro sound should play
                        # 1. just started chasing, or
                        # 2. switched to a different player target
                        should_play_sound = False
                        if not was_chasing and chasing_now:
                            should_play_sound = True
                        elif was_chasing and current_target_id is not None and current_target_id != last_sound_target_id:
                            should_play_sound = True
                        
                        
                        if should_play_sound:
                            comps[SoundRequest] = SoundRequest(
                                event="enemy_aggro",
                                subtype=size,
                                global_event=False,
                            )
                            ai.last_aggro_target_id = current_target_id
                        
                    else:
                        intent.move_x = 0.0
                        intent.move_y = 0.0
                
                if ai.kind == "projectileHoming":
                    # separated projectilehoming from chase because sounds should be different
                    pass

                elif ai.kind == "flee":
                
                    if dist < ai.agro_range and dist > 10:
                        intent.move_x = -dx / dist
                        intent.move_y = -dy / dist
                    else:
                        intent.move_x = 0.0
                        intent.move_y = 0.0

                #believed to work not sure tho
                elif ai.kind == "StraightLine":
                    if not hasattr(ai, "fixed_dir") and target_pos is not None:
                        # Calculate player direction at creation
                        dx0 = target_pos.x - pos.x
                        dy0 = target_pos.y - pos.y
                        d0 = max((dx0 * dx0 + dy0 * dy0) ** 0.5, 1.0)
                        ai.fixed_dir = (dx0 / d0, dy0 / d0)
                    
                    # Move along the fixed direction each frame
                    intent.move_x = ai.fixed_dir[0]
                    intent.move_y = ai.fixed_dir[1]

                elif ai.kind == "Range":


                    spawner = comps.get(ProjectileSpawner)
                    if not spawner:
                        continue

                    if dist > 10 and dist < ai.agro_range:  
                        intent.move_x = dx / dist
                        intent.move_y = dy / dist
                    else:
                        intent.move_x = 0.0
                        intent.move_y = 0.0


                    atk = comps.get(Attack)
                    if not atk or not target_pos:
                        continue

                    if not hasattr(ai, "shoot_timer"):
                         ai.shoot_timer = 0.0

                    ai.shoot_timer -= dt

                    if ai.shoot_timer <= 0.0:
                        ai.shoot_timer = 2.0  # shoot every 2 second        

                        if dist < ai.agro_range and dist > 10:
                            if world.get(entity_id, ProjectileRequest) is None:

                                spawn_kind =spawner.spawn_kind 
                                print("ProjectileRequest added for", entity_id)
                                world.add(
                                    entity_id,
                                    ProjectileRequest(target_pos=(target_pos.x, target_pos.y), spawn_kind=spawn_kind)
                                                                 
                                    
                                        )



        # optional: face target
            #intent.facing = "left" if dx < 0 else "right

            # facing
            if intent.move_x < -0.01:
                    intent.facing = "left"
            elif intent.move_x > 0.01:
                    intent.facing = "right"
