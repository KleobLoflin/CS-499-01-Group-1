# Class: App

# Entry point for the client, owns the Pygame window and the main loop
# possible fields: scene_manager, resources, clock, screen, running
# possible methods: run(), _process_events(), _fixed_update(dt), _draw()
# Calls into SceneManager.update() and draw(). This is where control returns every frame.

# (this will be the script to run to start the game client)

import sys, pygame
from game.core.config import Config
from game.core.time import FixedClock
from game.scene_manager import SceneManager
from game.scenes.dungeon import DungeonScene

def run() -> None:

    # init window and timing
    pygame.init()

    # get native screen resolution and compute scale
    info = pygame.display.Info()
    NATIVE_W = info.current_w
    NATIVE_H = info.current_h
    scale_w = NATIVE_W / Config.WINDOW_W
    scale_h = NATIVE_H / Config.WINDOW_H
    scale = min(scale_w, scale_h)
    scaled_width = int(Config.WINDOW_W * scale)
    scaled_height = int(Config.WINDOW_H * scale)

    pygame.display.set_caption(Config.WINDOW_TITLE)
    screen = pygame.display.set_mode((scaled_width, scaled_height))
    clock = pygame.time.Clock()
    fixed = FixedClock()

    # -----------------------------
    # create virtual surface at fixed resolution
    # -----------------------------
    base_surface = pygame.Surface((Config.WINDOW_W, Config.WINDOW_H))

    # this starts the dungeonscene for the movable rectangle
    # eventually the titlescreen would start first
    scenes = SceneManager()
    scenes.set(DungeonScene())

    # game loop #################################################################
    running = True
    while running:
        # 1) event checking
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                scenes.handle_event(event)

        # 2) update
        real_dt = clock.tick(Config.CLIENT_FPS) / 1000.0
        steps = fixed.step(real_dt, Config.FIXED_DT)
        for _ in range(steps):
            scenes.update(Config.FIXED_DT)

        # 3) Draw
        # draw everything to virtual surface first
        scenes.draw(base_surface)

        # scale virtual surface to native screen and blit
        scaled_surface = pygame.transform.scale(base_surface, (scaled_width, scaled_height))
        screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    run()
