import pygame
from pygame import Surface
from typing import Tuple
from game.world.title_components import TitleMenu

class TitleMenuSystem:
    def __init__(self, font: pygame.font.Font, pos_title: Tuple[int, int]=(40, 26), pos_options: Tuple[int, int]=(60, 110), line_h: int=28):
        self.font = font
        self.pos_title = pos_title
        self.pos_options = pos_options
        self.line_h = line_h

    def handle_event(self, world, event) -> None:
        for _, comps in world.query(TitleMenu):
            menu: TitleMenu = comps[TitleMenu]
            
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    menu.selected_index = (menu.selected_index - 1) % len(menu.options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    menu.selected_index = (menu.selected_index + 1) % len(menu.options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    select = menu.options[menu.selected_index].lower()
                    menu.selected_role = "host" if "host" in select else ("client" if "join" in select else "singleplayer")

    def update(self, world, dt: float) -> None:
        pass

    def draw_overlay(self, world, surface: Surface) -> None:
        for _, comps in world.query(TitleMenu):
            menu: TitleMenu = comps[TitleMenu]
            surface.blit(self.font.render(menu.title, True, (235, 235, 245)), self.pos_title)
            x, y = self.pos_options
            for i, text in enumerate(menu.options):
                selected = (i == menu.selected_index)
                color = (255, 255, 255) if selected else (175, 175, 185)
                prefix = "> " if selected else " "
                surface.blit(self.font.render(prefix + text, True, color), (x, y + i * self.line_h))