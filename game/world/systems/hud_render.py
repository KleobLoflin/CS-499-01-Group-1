import pygame
from pygame import Surface
from game.core.config import Config
from game.core.paths import resource_path
from game.world.components import Score, PlayerTag, Owner, LocalControlled, Life
from game.net.context import net


class HudRenderSystem:
    """
    HUD renderer.
    Current functionality:
    - Draws score for all players.
    - Draws hearts (hp) for all players.

    """
    FONT = None

    HEART_FULL = None
    HEART_HALF = None
    HEART_EMPTY = None

    def draw(self, world, surface: Surface) -> None:
        # Lazy init font (allowed, since no ECS/world state is stored)
        if HudRenderSystem.FONT is None:
            HudRenderSystem.FONT = pygame.font.SysFont("Retro Gaming", 20)

        # Heart asset check
        if HudRenderSystem.HEART_FULL is None:
            HudRenderSystem.HEART_FULL = pygame.image.load(
                resource_path("assets/ui/ui_heart_full.png")
            ).convert_alpha()
        if HudRenderSystem.HEART_HALF is None:
            HudRenderSystem.HEART_HALF = pygame.image.load(
                resource_path("assets/ui/ui_heart_half.png")
            ).convert_alpha()
        if HudRenderSystem.HEART_EMPTY is None:
            HudRenderSystem.HEART_EMPTY = pygame.image.load(
                resource_path("assets/ui/ui_heart_empty.png")
            ).convert_alpha()

        # Collect player scores
        scores = []  # list of tuples: (peer_id, score_value)
        c = 1   #count for player display

        for eid, comps in world.query(PlayerTag, Score, Owner):
            owner = comps[Owner].peer_id
            score = comps[Score].points
            scores.append((owner, score))

        # Sort so players always appear in a consistent order
        scores.sort(key=lambda x: str(x[0]))

        # Draw each player’s score vertically on the top-left
        x = 16
        y = 16
        padding = 22
  
        for owner_id, score in scores:
            label = f"Player {c}: {score}"
            img = HudRenderSystem.FONT.render(label, True, (255, 255, 255))
            surface.blit(img, (x, y))
            y += padding
            c += 1

        self._draw_player_health(world, surface)
        
    def _draw_player_health(self, world, surface: Surface) -> None:
        # Find local-controlled player with Life
        life_hp = None
        for _eid, comps in world.query(LocalControlled, Life):
            life_hp = comps[Life].hp
            max_hp = comps[Life].max_hp
            break

        if life_hp is None:
            return  # no local player yet

        # Clamp hp 
        max_hearts = int(max_hp / 2)
        hp = max(0, min(int(life_hp), max_hp))

        # Basic placement info
        full = HudRenderSystem.HEART_FULL
        half = HudRenderSystem.HEART_HALF
        empty = HudRenderSystem.HEART_EMPTY

        heart_w = full.get_width()
        heart_h = full.get_height()

        margin = 16
        spacing = 4  # pixels between hearts

        # Starting from the right edge, hearts extend left
        base_x = Config.WINDOW_W - margin
        y = margin

        for i in range(max_hearts):
            # Decide which image this heart should use
            heart_hp = hp - i * 2
            if heart_hp >= 2:
                img = full
            elif heart_hp == 1:
                img = half
            else:
                img = empty

            # Draw ith heart from right to left
            x = base_x - heart_w - i * (heart_w + spacing)
            surface.blit(img, (x, y))
