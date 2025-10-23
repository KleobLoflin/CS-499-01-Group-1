#calculates and transforms the screen to fit native resolution

import pygame
from game.core.config import Config

class Window:
    def __init__(self):
        # Get native resolution
        info = pygame.display.Info()
        self.native_w = info.current_w
        self.native_h = info.current_h

        # Calculate scale
        scale_w = self.native_w / Config.WINDOW_W
        scale_h = self.native_h / Config.WINDOW_H
        self.scale = min(scale_w, scale_h)

        # Scaled size
        self.scaled_width = int(Config.WINDOW_W * self.scale)
        self.scaled_height = int(Config.WINDOW_H * self.scale)

        # Create window + base surface
        pygame.display.set_caption(Config.WINDOW_TITLE)
        self.screen = pygame.display.set_mode((self.scaled_width, self.scaled_height))
        self.base_surface = pygame.Surface((Config.WINDOW_W, Config.WINDOW_H))

    def get_surface(self):
        #Return the virtual surface to draw onto.
        return self.base_surface

    def present(self):
        #Scale base surface to window and blit to screen.
        scaled_surface = pygame.transform.scale(
            self.base_surface, 
            (self.scaled_width, self.scaled_height)
        )
        self.screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()

