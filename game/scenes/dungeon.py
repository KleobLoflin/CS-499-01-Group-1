# Class DungeonScene(Scene)

# actual gameplay scene
# possible fields: world, net, hud, camera, local_player_id...
# possible methods: update(dt): send local inputs -> poll snapshots -> 
# client prediction/reconciliation -> world.update(dt).
# in draw(): render world -> HUD.

# the bridge between local presentation and server authority

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
    """
    Modular Step-1 scene:
      - Owns a World
      - Registers Systems in order: Input -> Movement
      - Spawns one "player" entity with Transform/Intent/DebugRect
      - Renders world entities (no rendering system yet; scenes draw)
    """
    def __init__(self) -> None:
        self.world = World()
        self.player_id: int | None = None

    def enter(self) -> None:
        # Spawn player entity
        self.player_id = self.world.new_entity()
        self.world.add(self.player_id, Transform(x=Config.WINDOW_W/2 - 16, y=Config.WINDOW_H/2 - 16))
        self.world.add(self.player_id, Intent())
        self.world.add(self.player_id, DebugRect(size=Config.RECT_SIZE, color=Config.RECT_COLOR))

        # Register systems (order matters)
        self.world.systems = [
            InputSystem(self.player_id),
            MovementSystem(),
            # later: CollisionSystem(), CombatSystem(), PresentationMapperSystem(), AnimationSystem(), ...
        ]

    def exit(self) -> None:
        pass

    def handle_event(self, event) -> None:
        pass  # chat/UI later; keyboard is read inside InputSystem

    def update(self, dt: float) -> None:
        self.world.update(dt)

    def draw(self, surface: Surface) -> None:
        surface.fill(Config.BG_COLOR)
        for _, comps in self.world.query(Transform, DebugRect):
            tr: Transform = comps[Transform]
            dr: DebugRect = comps[DebugRect]
            pygame.draw.rect(surface, dr.color, Rect(int(tr.x), int(tr.y), dr.size[0], dr.size[1]))
