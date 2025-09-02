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
    pygame.init()
    pygame.display.set_caption(Config.WINDOW_TITLE)
    screen = pygame.display.set_mode((Config.WINDOW_W, Config.WINDOW_H))
    clock = pygame.time.Clock()
    fixed = FixedClock()

    scenes = SceneManager()
    scenes.set(DungeonScene())  # start in gameplay for Step 1

    running = True
    while running:
        # 1) Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                scenes.handle_event(event)

        # 2) Fixed-timestep simulation
        real_dt = clock.tick(Config.CLIENT_FPS) / 1000.0
        steps = fixed.step(real_dt, Config.FIXED_DT)
        for _ in range(steps):
            scenes.update(Config.FIXED_DT)

        # 3) Draw
        scenes.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    run()
