import pygame
from pygame import Surface
from typing import Tuple
from game.world.components import TitleMenu, TitleIntro

class TitleMenuSystem:
    # def __init__(
    #         self, 
    #         title_font: pygame.font.Font,
    #         menu_font: pygame.font.Font,
    #         pos_title: Tuple[int, int]=(230, 72), 
    #         pos_options: Tuple[int, int]=(230, 175), 
    #         line_h: int=28):
    
    #     self.title_font = title_font
    #     self.menu_font = menu_font
    #     self.pos_title = pos_title
    #     self.pos_options = pos_options
    #     self.line_h = line_h

    # def handle_event(self, world, event) -> None:
    #     for _, comps in world.query(TitleMenu):
    #         menu: TitleMenu = comps[TitleMenu]
            
    #         if event.type == pygame.KEYDOWN:
    #             if event.key in (pygame.K_UP, pygame.K_w):
    #                 menu.selected_index = (menu.selected_index - 1) % len(menu.options)
    #             elif event.key in (pygame.K_DOWN, pygame.K_s):
    #                 menu.selected_index = (menu.selected_index + 1) % len(menu.options)
    #             elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
    #                 select = menu.options[menu.selected_index].lower()
    #                 menu.selected_role = "host" if "host" in select else ("client" if "join" in select else "singleplayer")

    # def update(self, world, dt: float) -> None:
    #     pass

    # def draw_overlay(self, world, surface: Surface) -> None:
    #     for _, comps in world.query(TitleMenu):
    #         menu: TitleMenu = comps[TitleMenu]
    #         surface.blit(self.title_font.render(menu.title, True, (235, 235, 245)), self.pos_title)
    #         x, y = self.pos_options
    #         for i, text in enumerate(menu.options):
    #             selected = (i == menu.selected_index)
    #             color = (255, 255, 255) if selected else (175, 175, 185)
    #             prefix = "> " if selected else " "
    #             surface.blit(self.menu_font.render(prefix + text, True, color), (x, y + i * self.line_h))

    import pygame
from pygame import Surface
from typing import List, Dict
from game.world.components import TitleMenu, TitleIntro

class TitleMenuSystem:
    """
    Pure-PNG title menu:
      - Input is ignored until TitleIntro.phase == 'ready'
      - Draws a full-screen PNG for the currently-selected option
      - Does NOT render any text; relies entirely on precomposited images
    """
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
        """
        Draw only the *options* full-screen image for the current selection.
        (The standalone logo fade is handled in the Scene.)
        This draws at full opacity; the Scene controls alpha by blitting via a buffer.
        """
        for _, comps in world.query(TitleMenu):
            menu: TitleMenu = comps[TitleMenu]
            img = self.options_images.get(menu.selected_index)
            if img:
                surface.blit(img, (0, 0))
