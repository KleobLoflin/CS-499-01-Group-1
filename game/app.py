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
    pygame.display.set_caption(Config.WINDOW_TITLE)
    screen = pygame.display.set_mode((Config.WINDOW_W, Config.WINDOW_H))
    clock = pygame.time.Clock()
    fixed = FixedClock()

    # this starts the dungeonscene for the movable rectangle
    # eventually the titlescreen would start first
    scenes = SceneManager()
    scenes.set(DungeonScene())

    # game loop #################################################################
    running = True
    while running:
        # 1) event checking
        for event in pygame.event.get():
            # stops program when you close the window
            if event.type == pygame.QUIT:
                running = False
            else:
                scenes.handle_event(event)

        # 2) update
        # gets delta time value used throughout program to control timing/framerate
        # dt explanation:
        # dt is smaller the higher the framerate and larger the lower the framerate
        # it is used to scale down or scale up movement speed of things on the screen
        # so that things always move at the same rate regardless of framerate.
        # without it, the game would play faster with a higher framerate and vice versa.
        real_dt = clock.tick(Config.CLIENT_FPS) / 1000.0
        # get fixed number of steps based on dt
        # gamestate is updated this many times each frame
        steps = fixed.step(real_dt, Config.FIXED_DT)
        for _ in range(steps):
            # update all game logic
            scenes.update(Config.FIXED_DT)

        # 3) Draw
        # draws everything to the screen each frame after logic update
        scenes.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    run()
