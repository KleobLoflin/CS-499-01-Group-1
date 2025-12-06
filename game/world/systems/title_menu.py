# AUTHORED BY: Scott Petty
import pygame
from pygame import Surface
from typing import List, Dict
from game.world.components import TitleMenu, TitleIntro

class TitleMenuSystem:
    def __init__(
        self,
        options_images: Dict[int, pygame.Surface],  # map selected_index -> full-screen Surface
    ):
        # Expected keys: 0..len(options)-1 matching TitleMenu.options order
        self.options_images = options_images

    def _intro_ready(self, world) -> bool:
        for _, comps in world.query(TitleIntro):
            return comps[TitleIntro].phase == "ready"
        return True

    def handle_event(self, world, event) -> None:
        if not self._intro_ready(world):
            return

        for _, comps in world.query(TitleMenu):
            menu: TitleMenu = comps[TitleMenu]
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    menu.selected_index = (menu.selected_index - 1) % len(menu.options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    menu.selected_index = (menu.selected_index + 1) % len(menu.options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    sel = menu.options[menu.selected_index].lower()
                    # map to your roles
                    if "host" in sel:
                        menu.selected_role = "host"
                    elif "join" in sel:
                        menu.selected_role = "client"
                    elif "settings" in sel:
                        menu.selected_role = "settings"
                    elif "quit" in sel:
                        menu.selected_role = "quit"
                    else:
                        menu.selected_role = "single_player"

    def update(self, world, dt: float) -> None:
        pass

    def draw_overlay(self, world, surface: Surface) -> None:
        for _, comps in world.query(TitleMenu):
            menu: TitleMenu = comps[TitleMenu]
            img = self.options_images.get(menu.selected_index)
            if img:
                surface.blit(img, (0, 0))
