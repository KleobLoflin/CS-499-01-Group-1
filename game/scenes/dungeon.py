# Class DungeonScene(Scene)

# actual gameplay scene
# possible fields: world, net, hud, camera, local_player_id...
# possible methods: update(dt): send local inputs -> poll snapshots -> 
# client prediction/reconciliation -> world.update(dt).
# in draw(): render world -> HUD.

# currently owns a world, registers systems in order, and draws entities

from game.scenes.base import Scene
import pygame
from pygame import Surface, Rect
from game.scene_manager import Scene
from game.core.config import Config
from game.world.world import World
from game.world.components import Transform, Intent, DebugRect
from game.world.systems.input import InputSystem
from game.world.systems.movement import MovementSystem

class DungeonScene(Scene):
    def __init__(self) -> None:
        self.world = World()
        self.player_id: int | None = None

    def enter(self) -> None:
        # Spawn player entity with components that it will use
        self.player_id = self.world.new_entity()
        self.world.add(self.player_id, Transform(x=Config.WINDOW_W/2 - 16, y=Config.WINDOW_H/2 - 16))
        self.world.add(self.player_id, Intent())
        self.world.add(self.player_id, DebugRect(size=Config.RECT_SIZE, color=Config.RECT_COLOR))

        # Register systems in the order they should run each tick (order matters)
        self.world.systems = [
            InputSystem(self.player_id),
            MovementSystem(),
            # later: CollisionSystem(), CombatSystem(), PresentationMapperSystem(), AnimationSystem(), ...
        ]

    # method to release resources
    def exit(self) -> None:
        pass

    # this will be used to handle chat/ui later
    def handle_event(self, event) -> None:
        pass 

    # one fixed simulation step, runs all systems in order
    def update(self, dt: float) -> None:
        self.world.update(dt)

    # currently clears the screen and draws any entity that has Transform and DebugRect components
    def draw(self, surface: Surface) -> None:
        surface.fill(Config.BG_COLOR)
        for _, comps in self.world.query(Transform, DebugRect):
            tr: Transform = comps[Transform]
            dr: DebugRect = comps[DebugRect]
            pygame.draw.rect(surface, dr.color, Rect(int(tr.x), int(tr.y), dr.size[0], dr.size[1]))
