# app.py
import sys
import pygame
import threading
from game.net.server import GameServer
from game.net.client import GameClient
from game.core.config import Config
from game.core.time import FixedClock
from game.scene_manager import SceneManager
from game.scenes.dungeon import DungeonScene
from game.core.window import Window
from game.core.resources import load_atlases
from game.world.actors.blueprint_index import load as load_blueprints
import socket

# -------------------------------------------------------------------
# Helper to detect LAN IP
def get_local_ip():
    """Returns the LAN IP of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# -------------------------------------------------------------------
# CONFIGURATION
# On host machine: set SERVER_MODE = True
# On client machine: set SERVER_MODE = False
SERVER_MODE = True   # <-- Change to True on host machine
HOST_IP = get_local_ip()  # LAN IP of the server (host machine)

# -------------------------------------------------------------------
def run_server():
    """Start server (blocking)."""
    server = GameServer(host="0.0.0.0")  # listen on all interfaces
    print(f"[App] Server running on {HOST_IP}")
    server.run()  # blocks, accepts clients, updates world

def run_client(host=HOST_IP):
    """Start a client and connect to the server."""
    pygame.init()
    window = Window()
    pygame.display.set_caption(Config.WINDOW_TITLE)
    clock = pygame.time.Clock()
    fixed = FixedClock()

    # virtual surface
    base_surface = pygame.Surface((Config.WINDOW_W, Config.WINDOW_H))

    # load assets
    load_atlases("data/sprites/atlases.json")
    load_blueprints("data/blueprints/heroes.json", "data/blueprints/enemies.json")

    # connect to server
    client = GameClient(host=host, port=50000)
    client.connect()

    # start dungeon scene
    scenes = SceneManager()
    scenes.set(DungeonScene(net_client=client))

    # main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                scenes.handle_event(event)

        real_dt = clock.tick(Config.CLIENT_FPS) / 1000.0
        steps = fixed.step(real_dt, Config.FIXED_DT)
        for _ in range(steps):
            scenes.update(Config.FIXED_DT)

        # draw
        scenes.draw(base_surface)
        scenes.draw(window.get_surface())
        window.present()
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

# -------------------------------------------------------------------
if __name__ == "__main__":
    if SERVER_MODE:
        run_server()
    else:
        run_client(host=HOST_IP)
