# AUTHORED BY: Scott Petty
# Class: App

# Entry point for the client, owns the Pygame window and the main loop
# possible fields: scene_manager, resources, clock, screen, running
# possible methods: run(), _process_events(), _fixed_update(dt), _draw()
# Calls into SceneManager.update() and draw(). This is where control returns every frame.

# (this will be the script to run to start the game client)

import sys, pygame
from game.core.config import Config
from game.core.time import FixedClock
from game.core.paths import resource_path
from game.scene_manager import SceneManager
from game.scenes.menu import TitleScene
from game.core.window import Window
from game.sound.audio import bootstrap_sounds
from game.core.resources import load_atlases
from game.world.actors.blueprint_index import load as load_blueprints

def run() -> None:

    # init window and timing
    pygame.init()
    window = Window()
    pygame.display.set_caption(Config.WINDOW_TITLE)
    clock = pygame.time.Clock()
    fixed = FixedClock()

    # create virtual surface at fixed resolution
    base_surface = pygame.Surface((Config.WINDOW_W, Config.WINDOW_H))

    # load assets, atlases, and blueprints
    bootstrap_sounds()
    load_atlases(resource_path("data/sprites/atlases.json"))
    load_blueprints(resource_path("data/blueprints/heroes.json"), resource_path("data/blueprints/enemies.json"))

    # this starts the title scene
    scenes = SceneManager()
    scenes.set(TitleScene(scenes))

    # game loop #################################################################
    running = True
    while running:
        # 1) event check for 
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

                # draw to base surface
        scenes.draw(window.get_surface())

        # present final scaled image
        window.present()

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    run()
