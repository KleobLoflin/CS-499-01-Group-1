# game/world/systems/scoring.py
# Stateless scoring system.
# Awards score when enemies die, using ScoreValue.amount.
# Score is stored only on heroes (who must have a Score component).

from typing import Optional
import math

from game.world.components import (
    Transform, Life, Damage, Score, ScoreValue,
    PlayerTag, LocalControlled, Owner, AI,
    LastHitBy, Scored
)


class ScoringSystem:
    # No __init__; system is stateless.
    
    def update(self, world, dt: float) -> None:
        self._process_deaths(world)

    # ------------------------------------------------------------------
    # Death → Score logic
    # ------------------------------------------------------------------
    def _process_deaths(self, world) -> None:
        for eid, comps in world.query(Transform, Life):
            life: Life = comps[Life]

            # Not dead → skip
            if life.hp > 0:
                continue

            # Already awarded score → skip
            if comps.get(Scored):
                continue

            # Determine killer
            scorer_eid = self._resolve_scorer(world, eid, comps)

            # Get score value from the enemy's ScoreValue component
            sv = comps.get(ScoreValue)
            points = sv.amount if sv else 0

            if scorer_eid is not None and points > 0:
                # Ensure the scorer has a Score component
                score_comp = world.get(scorer_eid, Score)
                if not score_comp:
                    world.add(scorer_eid, Score(points=0))
                    score_comp = world.get(scorer_eid, Score)

                score_comp.points += points
                print(f"[Scoring] Player {scorer_eid} earned {points} pts (now {score_comp.points})")

            # Mark the entity as scored so we don’t re-award
            if not world.get(eid, Scored):
                world.add(eid, Scored(reason="death"))

    # ------------------------------------------------------------------
    # Scorer resolution chaining
    # ------------------------------------------------------------------
    def _resolve_scorer(self, world, dead_eid: int, comps: dict) -> Optional[int]:
        """
        Order of heuristics:
        1. LastHitBy.attacker_eid
        2. Damage.owner_id
        3. Owner.peer_id → matching PlayerTag
        4. AI.target_id if pointing at a player
        5. Fallback: nearest local-controlled player
        """

        # --- 1) LastHitBy
        lhb = comps.get(LastHitBy)
        if lhb and getattr(lhb, "attacker_eid", None) is not None:
            att = lhb.attacker_eid
            resolved = self._resolve_attacker_entity(world, att)
            if resolved is not None:
                return resolved

        # --- 2) Damage.owner_id
        dmg = comps.get(Damage)
        if dmg and dmg.owner_id is not None:
            resolved = self._resolve_attacker_entity(world, dmg.owner_id)
            if resolved is not None:
                return resolved

        # --- 3) Owner.peer_id (on the dead entity)
        owner = comps.get(Owner)
        if owner and getattr(owner, "peer_id", None) is not None:
            peer_id = owner.peer_id
            for peid, pcomps in world.query(PlayerTag, Owner):
                if pcomps[Owner].peer_id == peer_id:
                    return peid

        # --- 4) AI.target_id
        ai = comps.get(AI)
        if ai and ai.target_id is not None:
            tid = ai.target_id
            if isinstance(tid, int) and world.get(tid, PlayerTag):
                return tid

        # --- 5) nearest local player fallback
        return self._nearest_local_player(world, comps)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_attacker_entity(self, world, attacker_id) -> Optional[int]:
        """
        Converts attacker entity → player entity.
        Handles projectiles via Owner.peer_id.
        """
        if not isinstance(attacker_id, int):
            return None

        # Direct player
        if world.get(attacker_id, PlayerTag):
            return attacker_id

        # Projectile or proxy with Owner(peer)
        owner = world.get(attacker_id, Owner)
        if owner and getattr(owner, "peer_id", None) is not None:
            peer = owner.peer_id
            for peid, pcomps in world.query(PlayerTag, Owner):
                if pcomps[Owner].peer_id == peer:
                    return peid

        return None

    def _nearest_local_player(self, world, comps) -> Optional[int]:
        tr = comps.get(Transform)
        if not tr:
            return None

        best = None
        bestd = 1e12

        for peid, pcomps in world.query(PlayerTag, LocalControlled, Transform):
            pt = pcomps[Transform]
            dx = pt.x - tr.x
            dy = pt.y - tr.y
            d = math.hypot(dx, dy)
            if d < bestd:
                bestd = d
                best = peid

        return best
