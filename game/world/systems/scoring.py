# game/world/systems/scoring.py
# Stateless ECS system that awards score for kills and chest opens.
# Only defines update(self, world, dt) and helper methods.

import math
from typing import Optional

from game.world.components import (
    Transform, Life, Damage, Scored, Score,
    PlayerTag, LocalControlled, Owner,
    WorldObject, ChestOpened, AI, LastHitBy
)


class ScoringSystem:
    # No __init__; system must be stateless.

    def update(self, world, dt: float) -> None:
        # Award points for dead entities (must run BEFORE death() system)
        self._score_deaths(world)

        # Award points for opened chests
        self._score_chests(world)

    # --------------------------
    # Helpers
    # --------------------------
    def _score_deaths(self, world) -> None:
        for eid, comps in world.query(Transform, Life):
            life: Life = comps[Life]

            # skip if not dead
            if life.hp > 0:
                continue

            # skip if already scored
            if comps.get(Scored):
                continue

            # Determine who should receive points
            scorer_eid = self._find_scorer_for_entity(world, eid, comps)

            # Compute points for this entity
            points = self._points_for_entity_on_death(world, eid, comps)

            if scorer_eid is not None:
                # ensure scorer has a Score component (use world.add, world.get)
                s = world.get(scorer_eid, Score)
                if not s:
                    # create Score component if missing
                    world.add(scorer_eid, Score(points=0))
                    s = world.get(scorer_eid, Score)

                # increment
                s.points += points
                print(f"[Scoring] Awarded {points} pts to entity {scorer_eid} (total {s.points}) for killing entity {eid}")
            else:
                print(f"[Scoring] {points} pts available for killing entity {eid} but no scorer resolved")

            # mark the dead entity so we don't award again
            if not world.get(eid, Scored):
                world.add(eid, Scored(reason="death"))

    def _score_chests(self, world) -> None:
        for eid, comps in world.query(WorldObject, ChestOpened):
            if comps.get(Scored):
                continue

            chest_opened: ChestOpened = comps[ChestOpened]
            opener = chest_opened.opener_eid

            points = 50  # default chest points

            if opener is not None:
                s = world.get(opener, Score)
                if not s:
                    world.add(opener, Score(points=0))
                    s = world.get(opener, Score)
                s.points += points
                print(f"[Scoring] Awarded {points} pts to entity {opener} for opening chest {eid}")
            else:
                local = self._find_local_player_entity(world)
                if local is not None:
                    s = world.get(local, Score)
                    if not s:
                        world.add(local, Score(points=0))
                        s = world.get(local, Score)
                    s.points += points
                    print(f"[Scoring] Awarded {points} pts to local entity {local} for opening chest {eid} (no opener provided)")
                else:
                    print(f"[Scoring] Chest {eid} opened but no opener found; {points} pts unassigned")

            if not world.get(eid, Scored):
                world.add(eid, Scored(reason="chest"))

    def _find_scorer_for_entity(self, world, dead_eid: int, comps: dict) -> Optional[int]:
        """
        Resolve which player/entity should receive credit for killing `dead_eid`.
        Order of heuristics:
          1) LastHitBy.attacker_eid (set by AttackSystem)
          2) Damage.owner_id (component on the dead entity)
          3) Owner.peer_id -> find player entity with matching Owner.peer_id
          4) AI.target_id if it points to a player entity
          5) nearest LocalControlled player
        """

        # 1) LastHitBy (preferred; set by attack system)
        lhb = comps.get(LastHitBy)
        if lhb and getattr(lhb, "attacker_eid", None) is not None:
            attacker = lhb.attacker_eid
            # if attacker is a projectile or proxy, try to resolve its Owner -> player
            if isinstance(attacker, int):
                # if attacker itself is a player, return it
                if world.get(attacker, PlayerTag):
                    return attacker
                # else, check if attacker has an Owner component linking to a peer/player
                owner = world.get(attacker, Owner)
                if owner and getattr(owner, "peer_id", None) is not None:
                    # prefer the player entity that has Owner.peer_id == owner.peer_id
                    for peid, pcomps in world.query(PlayerTag, Owner):
                        own = pcomps.get(Owner)
                        if own and own.peer_id == owner.peer_id:
                            return peid
                # else, maybe the projectile recorded the real player id in a field named 'shooter' or similar:
                # (skip—projectile conventions vary; user can extend this)
            # otherwise, if it's not an int it's unexpected; ignore

        # 2) Damage.owner_id
        dmg = comps.get(Damage)
        if dmg and getattr(dmg, "owner_id", None) is not None:
            owner_id = dmg.owner_id
            if isinstance(owner_id, int):
                if world.get(owner_id, PlayerTag):
                    return owner_id
                # if it's an entity that's not a player, try to find its Owner.peer_id -> player
                owner_comp = world.get(owner_id, Owner)
                if owner_comp and getattr(owner_comp, "peer_id", None) is not None:
                    for peid, pcomps in world.query(PlayerTag, Owner):
                        own = pcomps.get(Owner)
                        if own and own.peer_id == owner_comp.peer_id:
                            return peid
            if isinstance(owner_id, str):
                # owner_id is a peer-id string, find player with that Owner.peer_id
                for peid, pcomps in world.query(PlayerTag, Owner):
                    own = pcomps.get(Owner)
                    if own and own.peer_id == owner_id:
                        return peid

        # 3) Owner.peer_id directly on dead entity (rare)
        owner_comp = comps.get(Owner)
        if owner_comp and getattr(owner_comp, "peer_id", None) is not None:
            peer_id = owner_comp.peer_id
            for peid, pcomps in world.query(PlayerTag, Owner):
                own = pcomps.get(Owner)
                if own and own.peer_id == peer_id:
                    return peid

        # 4) AI.target_id (if the AI was targeting the killer player)
        ai = comps.get(AI)
        if ai and getattr(ai, "target_id", None) is not None:
            tid = ai.target_id
            if isinstance(tid, int) and world.get(tid, PlayerTag):
                return tid

        # 5) Heuristic fallback: pick nearest LOCAL player (if available)
        transform = comps.get(Transform)
        if transform:
            best = None
            bestd = 1e9
            for peid, pcomps in world.query(PlayerTag, LocalControlled, Transform):
                pt = pcomps.get(Transform)
                dx = pt.x - transform.x
                dy = pt.y - transform.y
                d = math.hypot(dx, dy)
                if d < bestd:
                    bestd = d
                    best = peid
            if best is not None:
                return best

        # Nothing matched
        return None

    def _points_for_entity_on_death(self, world, eid: int, comps: dict) -> int:
        try:
            life = comps.get(Life)
            if life and life.hp is not None:
                if abs(life.hp) > 5:  # scaled score
                    return max(10, int(abs(life.hp) * 20))
        except Exception:
            pass
        return 100  # default

    def _find_local_player_entity(self, world) -> Optional[int]:
        for peid, pcomps in world.query(PlayerTag, LocalControlled):
            return peid
        return None
