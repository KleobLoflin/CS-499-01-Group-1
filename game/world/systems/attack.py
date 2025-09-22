from game.world.components import Intent, Attack

class AttackSystem:
    def update(self, world, dt):
        for eid, comps in world.query(Intent, Attack):
            it: Intent = comps[Intent]
            atk: Attack = comps[Attack]

            # get attacking status from intent
            if it.basic_atk:
                atk.active = True
                if atk.remaining_cooldown <= 0.0:
                    it.basic_atk = False
                    atk.active = False
                    atk.remaining_cooldown = atk.max_cooldown
                else:
                    atk.remaining_cooldown -= dt
            