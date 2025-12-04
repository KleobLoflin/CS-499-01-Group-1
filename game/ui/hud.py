# game/ui/hud.py
import pygame
from game.world.components import PlayerTag, LocalControlled, Score

class HUD:

    _font = None   # static cached font

    def _ensure_font(self):
        # Initialize once, statically, without requiring __init__
        if HUD._font is None:
            pygame.font.init()
            HUD._font = pygame.font.Font(None, 28)

    def update(self, world, dt):
        # HUD has no state updates, but we ensure the font exists
        self._ensure_font()

    def render(self, screen, world, camera):
        self._ensure_font()

        # -----------------------------
        # 1. Find local player
        # -----------------------------
        player_eid = None
        for eid, comps in world.query(PlayerTag, LocalControlled):
            player_eid = eid
            break

        # -----------------------------
        # 2. Get the score
        # -----------------------------
        points = 0
        if player_eid is not None:
            score = world.get(player_eid, Score)
            if score:
                points = score.points

        # -----------------------------
        # 3. Draw score
        # -----------------------------
        surf = HUD._font.render(f"Score: {points}", True, (255, 255, 0))
        screen.blit(surf, (12, 12))
