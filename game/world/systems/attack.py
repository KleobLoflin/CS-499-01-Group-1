from game.world.components import Intent, Attack, Transform, HitboxSize, PlayerTag, AI, Life
import math

class AttackSystem:
    def __init__(self, swing_duration: float = 0.2, swing_length: float = 20.0):
        self.swing_duration = swing_duration
        self.swing_length = swing_length
        self.swing_progress = {}
        self.already_hit = {}
        self.knockbacks = {}  # reuse the same structure as CollisionSystem

    def update(self, world, dt):
        for eid, comps in world.query(Intent, Attack, Transform):
            it: Intent = comps[Intent]
            atk: Attack = comps[Attack]
            tr: Transform = comps[Transform]
            

            if it.basic_atk and atk.remaining_cooldown <= 0.0:
                atk.active = True
                it.basic_atk = False
                atk.remaining_cooldown = atk.max_cooldown
                self.swing_progress[eid] = 0.0
                self.already_hit[eid] = set()

            # handle swing progression
            if atk.active:
                self.swing_progress[eid] += dt
                progress = self.swing_progress[eid] / self.swing_duration

                if progress >= 1.0:
                    atk.active = False
                    self.swing_progress[eid] = 0.0
                    self.already_hit[eid].clear()
                    continue

                facing = getattr(it, "facing", "down")

                swing_arcs = {
                    "up": (-135, -45),
                    "down": (135, 45),
                    "right": (135, 45),
                    "left": (45, 225),
                }

                start_angle, end_angle = swing_arcs.get(facing, (135, 45))
                swing_angle = start_angle + (end_angle - start_angle) * progress
                swing_radians = math.radians(swing_angle)

                # sword tip position
                sx = tr.x + math.cos(swing_radians) * self.swing_length
                sy = tr.y + math.sin(swing_radians) * self.swing_length

                hit_this_frame = set()

                # check for hits
                for enemy_id, enemy_comps in world.query(Transform, AI, HitboxSize):
                    enemy_tr: Transform = enemy_comps[Transform]
                    enemy_hitbox: HitboxSize = enemy_comps[HitboxSize]

                    


                    
                    if self._line_hit(tr.x, tr.y, sx, sy, enemy_tr.x, enemy_tr.y, enemy_hitbox.radius):
                        hit_this_frame.add(enemy_id)

                # register knockback only once per swing
                for enemy_id in hit_this_frame:
                    if enemy_id not in self.already_hit[eid]:
                        enemy_life = world.get(enemy_id, Life)
                    

                        if enemy_life:
                            enemy_life.hp -= atk.damage
                            print(f"Enemy {enemy_id} HP: {enemy_life.hp}")
                            #print(f"{enemy_id} hit")

                     

                        # compute knockback direction (from player to enemy)
                        enemy_tr = world.get(enemy_id, Transform)
                        dx = enemy_tr.x - tr.x
                        dy = enemy_tr.y - tr.y
                        dist = math.hypot(dx, dy)
                        if dist != 0:
                            dx /= dist
                            dy /= dist

                        # register knockback (same as CollisionSystem)
                        self.knockbacks[enemy_id] = {"timer": 0.2, "dir": (dx, dy)}

                        self.already_hit[eid].add(enemy_id)

            # cooldown timer
            if atk.remaining_cooldown > 0.0:
                atk.remaining_cooldown -= dt

        # apply knockback motion (identical logic to CollisionSystem)
        expired = []
        for enemy_id, state in self.knockbacks.items():
            if state["timer"] > 0:
                state["timer"] -= dt
                tr = world.get(enemy_id, Transform)
                if tr:
                    strength = 500 * (state["timer"] / 0.2)  # use Config.KNOCKBACK_STRENGTH if defined
                    tr.x += state["dir"][0] * strength * dt
                    tr.y += state["dir"][1] * strength * dt
            else:
                expired.append(enemy_id)

        for enemy_id in expired:
            del self.knockbacks[enemy_id]

    def _line_hit(self, x1, y1, x2, y2, cx, cy, radius):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return False
        t = ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        dist = math.hypot(closest_x - cx, closest_y - cy)
        return dist <= radius + 8.0
