# AUTHORED BY: Matthew Payne
# EDITED BY: Scott Petty

from game.world.components import Intent, Attack, Transform, HitboxSize, PlayerTag, AI, Life, OnMap, LastHitBy, SoundRequest
from game.sound.enemy_sound_utils import infer_enemy_size
import math



class AttackSystem:
    """
    Anim-matched swings:
      RIGHT/LEFT ~210°: starts slightly behind, ends slightly past forward.
      DOWN ~225°: start up (270°) → ~45° right of straight down (~135°).
      UP   ~225°: start bottom (90°) → above head ~45° right (315°).

    0° = right, 90° = down, 180° = left, 270° = up. Interpolate CCW with wrap.

    Implementation notes:
    - We test BOTH the instantaneous blade (origin→tip) AND the swept arc segment
      for this frame (prev_tip→tip). This fixes misses near 270–360° where the
      angle changes quickly.
    """

    def __init__(
        self,
        swing_duration: float = 0.20,
        swing_length: float = 16.0,
        hand_offset: float = 2.0,
        hit_padding: float = 2.0,     # small forgiveness
        swing_speed: float = 1.25,    # sync with animation
        arc_gain: float = 1.06,       # slight extra sweep
        reach_bias: dict | None = None,
    ):
        self.swing_duration = swing_duration
        self.swing_length = swing_length
        self.swing_progress = {}
        self.already_hit = {}
        self.knockbacks = {}

        # global tuning
        self.HAND_OFFSET = float(hand_offset)
        self.HIT_PADDING = float(hit_padding)
        self.SWING_SPEED = float(swing_speed)
        self.ARC_GAIN = float(arc_gain)

        # let the whole blade register 
        self.OUTER_FRACTION = 0.0

        # per-facing fine-tunes 
        self.REACH_BIAS = reach_bias or {"up": 0.0, "right": 0.0, "down": 0.0, "left": 2.0}
        self.FORWARD_BIAS_BY_FACING = {"up": 0.0, "right": 0.0, "down": 0.0, "left": 0.75}
        self.ARC_GAIN_BY_FACING = {"up": 1.0, "right": 1.0, "down": 1.0, "left": 1.20}

        self.prev_tip = {}  

    @staticmethod
    def _deg_to_rad(deg: float) -> float:
        return math.radians(deg % 360.0)

    @staticmethod
    def _ccw_span(start_deg: float, end_deg: float) -> float:
        end = end_deg
        if end <= start_deg:
            end += 360.0
        return end - start_deg

    def update(self, world, dt):
        for eid, comps in world.query(Intent, Attack, Transform):
            it: Intent = comps[Intent]
            atk: Attack = comps[Attack]
            tr: Transform = comps[Transform]

            # start swing
            wants_attack = it.basic_atk or it.basic_atk_held
            if wants_attack and atk.remaining_cooldown <= 0.0:
                atk.active = True
                it.basic_atk = False
                atk.remaining_cooldown = atk.max_cooldown
                self.swing_progress[eid] = 0.0
                self.already_hit[eid] = set()
                self.prev_tip[eid] = None
                self.prev_tip[eid] = None

                # attack sound request
                if PlayerTag in comps:
                    comps[SoundRequest] = SoundRequest(event="player_swing")

            if atk.active:
                self.swing_progress[eid] += dt
                # speed up interpolation to match animation (Adjust if enemies are hit too late or soon)
                progress = (self.swing_progress[eid] / self.swing_duration) * self.SWING_SPEED
                if progress >= 1.0:
                    atk.active = False
                    self.swing_progress[eid] = 0.0
                    self.already_hit[eid].clear()
                    self.prev_tip.pop(eid, None)
                    continue

                facing = getattr(it, "facing", "down")

                # base arcs
                base_arcs = {
                    "right": (195.0,  45.0),  
                    "left":  (300.0, 195.0),  
                    "down":  (270.0, 135.0),  
                    "up":    ( 90.0, 315.0),  
                }
                start_deg, end_deg = base_arcs.get(facing, (195.0, 45.0))

                base_span = self._ccw_span(start_deg, end_deg)
                span = base_span * (self.ARC_GAIN * self.ARC_GAIN_BY_FACING.get(facing, 1.0))

                angle_deg = (start_deg + span * progress) % 360.0
                ang = self._deg_to_rad(angle_deg)

                # Offset the origin point of the arc
                hand_offsets = {
                    "up":    (0.0, -self.HAND_OFFSET),
                    "right": (self.HAND_OFFSET, 0.0),
                    "down":  (0.0, self.HAND_OFFSET),
                    "left":  (-self.HAND_OFFSET, 0.0),
                }
                ox, oy = hand_offsets.get(facing, (0.0, 0.0))

                fb = self.FORWARD_BIAS_BY_FACING.get(facing, 0.0)
                fx, fy = {
                    "up":    (0.0, -fb),
                    "right": (fb, 0.0),
                    "down":  (0.0, fb),
                    "left":  (-fb, 0.0),
                }[facing]

                origin_x = tr.x + ox + fx
                origin_y = tr.y + oy + fy

                length = self.swing_length + self.REACH_BIAS.get(facing, 0.0)
                sx = origin_x + math.cos(ang) * length
                sy = origin_y + math.sin(ang) * length

                prev = self.prev_tip.get(eid)
                if prev is None:
                    prev = (sx, sy)
                self.prev_tip[eid] = (sx, sy)
                
                # restrict hits to enemies on the same map as the attacker
                attacker_on = world.get(eid, OnMap)
                attacker_map_id = attacker_on.id if attacker_on is not None else None

                hit_this_frame = set()
                for enemy_id, enemy_comps in world.query(Transform, AI, HitboxSize):
                    if attacker_map_id is not None:
                        enemy_on = world.get(enemy_id, OnMap)
                        if enemy_on is None or enemy_on.id != attacker_map_id:
                            continue
                    enemy_tr: Transform = enemy_comps[Transform]
                    enemy_hitbox: HitboxSize = enemy_comps[HitboxSize]

                    hit_now = self._line_hit(origin_x, origin_y, sx, sy,
                                             enemy_tr.x, enemy_tr.y, enemy_hitbox.radius)
                    hit_swept = self._line_hit(prev[0], prev[1], sx, sy,
                                               enemy_tr.x, enemy_tr.y, enemy_hitbox.radius)

                    if hit_now or hit_swept:
                        hit_this_frame.add(enemy_id)

                # apply once per swing per target
                for enemy_id in hit_this_frame:
                    if enemy_id not in self.already_hit[eid]:
                        enemy_life = world.get(enemy_id, Life)
                        enemy_ai: AI | None = world.get(enemy_id, AI)

                        if enemy_life:
                            old_hp = enemy_life.hp
                            enemy_life.hp -= atk.damage
                            new_hp = enemy_life.hp
                            
                            # attach sound request
                            enemy_comps = world.components_of(enemy_id)

                            if old_hp > 0 and new_hp <= 0:
                                # enemy death
                                enemy_comps[SoundRequest] = SoundRequest(
                                    event="enemy_death",
                                    subtype=enemy_ai.size,
                                    global_event=False,
                                )

                            elif new_hp < old_hp:
                                # enemy hit but still alive
                                enemy_comps[SoundRequest] = SoundRequest(
                                    event="enemy_hit",
                                    subtype=enemy_ai.size,
                                    global_event=False,
                                )

                            existing = world.get(enemy_id, LastHitBy)
                            if existing:
                                existing.attacker_eid = eid
                            else:
                                world.add(enemy_id, LastHitBy(attacker_eid=eid))

                        enemy_tr = world.get(enemy_id, Transform)
                        dx = enemy_tr.x - tr.x
                        dy = enemy_tr.y - tr.y
                        dist = math.hypot(dx, dy)
                        if dist != 0:
                            dx /= dist
                            dy /= dist

                        self.knockbacks[enemy_id] = {"timer": 0.2, "dir": (dx, dy)}
                        self.already_hit[eid].add(enemy_id)

            if atk.remaining_cooldown > 0.0:
                atk.remaining_cooldown -= dt

        # knockback 
        expired = []
        for enemy_id, state in list(self.knockbacks.items()):
            if state["timer"] > 0:
                state["timer"] -= dt
                tr = world.get(enemy_id, Transform)
                if tr:
                    strength = 500 * (state["timer"] / 0.2)
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
        t = max(self.OUTER_FRACTION, min(1.0, t))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        dist = math.hypot(closest_x - cx, closest_y - cy)
        return dist <= radius + self.HIT_PADDING
