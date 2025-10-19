# Class: Menu(Scene)

# Title screen menu, start/pause menu, etc...
# controls game menus and when a player selects an option, tells scene_manager to switch
# to the appropriate scene.

# example: on title screen: if player selects "start", asks scene_manager to swtich to hub scene

from game.scenes.base import Scene
import pygame
from pygame import Surface

from game.scenes.dungeon import DungeonScene
from game.world.world import World
from game.world.components import TitleMenu, SpawnPolicy, TitleIntro
from game.world.systems.title_menu import TitleMenuSystem
from game.world.systems.render import RenderSystem
from game.world.systems.animation import AnimationSystem
from game.world.systems.presentation_mapper import PresentationMapperSystem
from game.world.systems.movement import MovementSystem
from game.world.systems.collision import CollisionSystem
from game.world.systems.spawn import SpawnSystem

from game.world.maps.map_index import load_registry, pick
from game.world.maps.map_factory import create_or_activate

class TitleScene(Scene):
    # def __init__(self, scene_manager):
    #     self.sm = scene_manager
    #     self.world = World()

    #     # title menu system to run in event handler
    #     pygame.font.init()
    #     self.menu_ui = TitleMenuSystem(pygame.font.SysFont("consolas", 28), pygame.font.SysFont("consolas", 20))

    #     # render system runs in draw function, not with logic systems
    #     self.render = RenderSystem()

    # def enter(self) -> None:
    #     # Registry once
    #     load_registry("data/map_registry.json")

    #     # pick any map tagged "title_ok" (weighted)
    #     mi = pick(require_all=["title_ok"])
    #     create_or_activate(self.world, mi.id)

    #     # title menu singleton
    #     eid = self.world.new_entity()
    #     self.world.add(eid, TitleMenu(title="Gate Crashers"))

    #     # Tell SpawnSystem to run ONLY title spawns (not gameplay)
    #     cfg = self.world.new_entity()
    #     self.world.add(cfg, SpawnPolicy(
    #         run_title_spawns=True,
    #         run_game_spawns=False,
    #         spawn_player=False
    #     ))

    #     # register logic systems in order
    #     self.world.systems = [
    #         PresentationMapperSystem(),
    #         AnimationSystem(),
    #         MovementSystem(),
    #         CollisionSystem(),   
    #         SpawnSystem(),       
    #         self.menu_ui,
    #     ]
    
    # def exit(self) -> None:
    #     pass

    # def handle_event(self, event) -> None:
    #     # Titlemenu system runs in event handler and takes care of input
    #     self.menu_ui.handle_event(self.world, event)

    # def update(self, dt: float) -> None:
    #     self.world.update(dt)

    #     # if player chose a role, swap scenes
    #     for _, comps in self.world.query(TitleMenu):
    #         menu: TitleMenu = comps[TitleMenu]

    #         if menu.selected_role:
    #             self.sm.set(DungeonScene(role=menu.selected_role))
    #             return
    
    # def draw(self, surface: Surface) -> None:
    #     self.render.draw(self.world, surface)
    #     self.menu_ui.draw_overlay(self.world, surface)

    """
    Sequence:
      1) Standalone logo fades in (logo.png)
      2) After hold, gameplay + menu (full-screen options image) fade in underneath
      3) When ready, input enables; selecting transitions to next scene/role
    """
    def __init__(self, scene_manager):
        self.sm = scene_manager
        self.world = World()

        # --- Load PNG assets (all 640x360 precomposited) ---
        # 1 logo:
        self.logo_img = pygame.image.load("assets/ui/title_screen/logo/logo.png").convert_alpha()

        # 5 option-state screens, indexed by TitleMenu.selected_index order:
        #   0: Single Player, 1: Host, 2: Join, 3: Settings, 4: Quit
        self.options_imgs = {
            0: pygame.image.load("assets/ui/title_screen/menu/single_player.png").convert_alpha(),
            1: pygame.image.load("assets/ui/title_screen/menu/host.png").convert_alpha(),
            2: pygame.image.load("assets/ui/title_screen/menu/join.png").convert_alpha(),
            3: pygame.image.load("assets/ui/title_screen/menu/settings.png").convert_alpha(),
            4: pygame.image.load("assets/ui/title_screen/menu/quit.png").convert_alpha(),
        }

        # menu system (pure-PNG)
        self.menu_ui = TitleMenuSystem(options_images=self.options_imgs)

        # renderer for gameplay layer
        self.render = RenderSystem()

        # alpha layering buffers
        self._bg_buf = None   # gameplay + menu
        self._ui_buf = None   # menu only (kept separate for clarity)

    def enter(self) -> None:
        # Registry once
        load_registry("data/map_registry.json")

        # pick any map tagged "title_ok" (weighted)
        mi = pick(require_all=["title_ok"])
        create_or_activate(self.world, mi.id)

        # Title menu singleton
        eid = self.world.new_entity()
        self.world.add(eid, TitleMenu(
            options=["single_player", "host", "join", "settings", "quit"],
            selected_index=0
        ))

        # Intro controller singleton (fade timings are in the component)
        intro = self.world.new_entity()
        self.world.add(intro, TitleIntro())

        # Title-only spawn policy
        cfg = self.world.new_entity()
        self.world.add(cfg, SpawnPolicy(
            run_title_spawns=True,
            run_game_spawns=False,
            spawn_player=False
        ))

        # logic systems
        self.world.systems = [
            PresentationMapperSystem(),
            AnimationSystem(),
            MovementSystem(),
            CollisionSystem(),
            SpawnSystem(),
            self.menu_ui,
        ]

    def exit(self) -> None:
        pass

    def handle_event(self, event) -> None:
        self.menu_ui.handle_event(self.world, event)

    def _update_intro(self, dt: float) -> None:
        
        
        def smoothstep01(x: float) -> float:
            x = max(0.0, min(1.0, x))
            return x * x * (3.0 - 2.0 * x)

        for _, comps in self.world.query(TitleIntro):
            tr = comps[TitleIntro]
            tr.t += dt

            if tr.phase == "pre_delay":
                tr.logo_alpha = 0
                tr.bg_alpha = 0
                if tr.t >= tr.pre_delay_dur:
                    tr.phase = "logo_fade"
                    tr.t = 0.0

            elif tr.phase == "logo_fade":
                p = smoothstep01(tr.t / tr.logo_fade_dur)
                tr.logo_alpha = int(p * 255)
                tr.bg_alpha = 0
                if tr.t >= tr.logo_fade_dur:
                    tr.phase = "hold"
                    tr.t = 0.0
                    tr.logo_alpha = 255

            elif tr.phase == "hold":
                tr.logo_alpha = 255
                tr.bg_alpha = 0
                if tr.t >= tr.logo_hold_dur:
                    tr.phase = "bg_fade"
                    tr.t = 0.0

            elif tr.phase == "bg_fade":
                tr.logo_alpha = 255
                p = smoothstep01(tr.t / tr.bg_fade_dur)
                tr.bg_alpha = int(p * 255)
                if tr.t >= tr.bg_fade_dur:
                    tr.phase = "ready"
                    tr.t = 0.0
                    tr.bg_alpha = 255

            elif tr.phase == "ready":
                tr.logo_alpha = 255
                tr.bg_alpha = 255


    def update(self, dt: float) -> None:
        self._update_intro(dt)
        self.world.update(dt)

        # if player chose a role, swap scenes
        for _, comps in self.world.query(TitleMenu):
            menu: TitleMenu = comps[TitleMenu]
            if menu.selected_role:
                # handle quit/settings specially if needed; default to DungeonScene
                if menu.selected_role == "quit":
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                    return
                elif menu.selected_role == "settings":
                    # TODO: push your SettingsScene() instead if you have one
                    return
                else:
                    self.sm.set(DungeonScene(role=menu.selected_role))
                    return

    def _ensure_buffers(self, surface: Surface) -> None:
        if self._bg_buf is None or self._bg_buf.get_size() != surface.get_size():
            w, h = surface.get_size()
            self._bg_buf = pygame.Surface((w, h), flags=pygame.SRCALPHA).convert_alpha()
            self._ui_buf = pygame.Surface((w, h), flags=pygame.SRCALPHA).convert_alpha()

    def draw(self, surface: Surface) -> None:
        self._ensure_buffers(surface)

        # Clear buffers
        self._bg_buf.fill((0, 0, 0, 0))
        self._ui_buf.fill((0, 0, 0, 0))

        # Draw gameplay into bg buffer
        self.render.draw(self.world, self._bg_buf)

        # Draw current options image into ui buffer (full opacity here)
        for _, comps in self.world.query(TitleMenu):
            menu: TitleMenu = comps[TitleMenu]
            img = self.options_imgs.get(menu.selected_index)
            if img:
                self._ui_buf.blit(img, (0, 0))
            break

        # Read alphas from TitleIntro
        logo_alpha = 255
        bg_alpha = 255
        phase = "ready"
        for _, comps in self.world.query(TitleIntro):
            intro: TitleIntro = comps[TitleIntro]
            logo_alpha = intro.logo_alpha
            bg_alpha = intro.bg_alpha
            phase = intro.phase
            break

        # 1) Background gameplay (fades in with bg_alpha)
        self._bg_buf.set_alpha(bg_alpha)
        surface.blit(self._bg_buf, (0, 0))

        # 2) Options screen (also fades in with bg_alpha)
        self._ui_buf.set_alpha(bg_alpha)
        surface.blit(self._ui_buf, (0, 0))

        # 3) Standalone logo: ALWAYS draw (fade in, then stay visible)
        if logo_alpha != 255:
            logo = self.logo_img.copy()
            logo.set_alpha(logo_alpha)
        else:
            logo = self.logo_img
        surface.blit(logo, (0,0))