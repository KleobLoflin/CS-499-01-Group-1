import pygame
from pygame import Surface
from game.world.components import Score, PlayerTag, Owner
from game.net.context import net


class HudRenderSystem:
    """
    HUD renderer.
    Current functionality:
    - Draws score for all players.

    """
    FONT = None

    def draw(self, world, surface: Surface) -> None:
        # Lazy init font (allowed, since no ECS/world state is stored)
        if HudRenderSystem.FONT is None:
            HudRenderSystem.FONT = pygame.font.SysFont("Retro Gaming", 20)

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
