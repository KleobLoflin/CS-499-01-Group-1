import threading
import pygame
from game.net.server import GameServer
from game.scenes.dungeon import DungeonScene
from game.scene_manager import SceneManager

# --- Server setup ---
server = GameServer(host="127.0.0.1", port=50000)

def run_server():
    server.run()  # blocking, runs server loop

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
print("Server started on 127.0.0.1:50000")

# --- Client setup ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Dungeon Multiplayer Test")
clock = pygame.time.Clock()

# Create a SceneManager to hold the scene
scene_manager = SceneManager()
dungeon_scene = DungeonScene()
scene_manager.push(dungeon_scene)
dungeon_scene.enter()

# --- Main loop ---
running = True
while running:
    dt = clock.tick(60) / 1000.0  # delta time in seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        dungeon_scene.handle_event(event)

    dungeon_scene.update(dt)
    dungeon_scene.draw(screen)

    pygame.display.flip()

pygame.quit()
