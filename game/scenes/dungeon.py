# Class DungeonScene(Scene)

# actual gameplay scene
# possible fields: world, net, hud, camera, local_player_id...
# possible methods: update(dt): send local inputs -> poll snapshots -> 
# client prediction/reconciliation -> world.update(dt).
# in draw(): render world -> HUD.

# currently owns a world, registers systems in order, and draws entities

from game.scenes.base import Scene
import pygame
import pytmx
from pygame import Surface, Rect
from game.scene_manager import Scene
from game.core.config import Config
from game.world.world import World
from game.world.components import Transform, Intent, DebugRect, MoveSpeed
from game.world.actors.hero_factory import create as create_hero
from game.world.actors.enemy_factory import create as create_enemy
from game.world.systems.input import InputSystem
from game.world.systems.movement import MovementSystem
from game.world.systems.ai import EnemyAISystem
from game.world.systems.room import draw_map

class DungeonScene(Scene):
    def __init__(self) -> None:
        self.world = World()
        self.player_id: int | None = None
        tmx_path = "assets/maps/testmap.tmx"
        self.world.tmx_data = pytmx.load_pygame(tmx_path)

    def enter(self) -> None:
        # Spawn player entity with components that it will use
        self.player_id = create_hero(self.world, archetype="knight", owner_client_id=None, pos=(Config.WINDOW_W/2 - 16, Config.WINDOW_H/2 - 16))

        #Spawn chase enemy entity with components that it will use
        self.chaser_1_id = create_enemy(self.world, kind="chase", pos=(100, 100), params={"color": (255, 0, 0), "speed" : 160, "target_id" : self.player_id})

        #spawn flee enemy entity with components that it will use
        self.flee_1_id = create_enemy(self.world, kind="flee", pos=(200, 100), params={"color": (255, 255, 0), "speed" : 160, "target_id" : self.player_id})

        #spawn wonder enemy curently is just a crackhead vibrairting violently
        self.wander_1_id = create_enemy(self.world, kind="wander", pos=(200, 200), params={"color": (255, 0, 255), "speed" : 160})

        # Register systems in the order they should run each tick (order matters)
        self.world.systems = [
            InputSystem(self.player_id),
            EnemyAISystem(),   # <-- AI runs every frame
            MovementSystem()
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
        draw_map(surface, self.world.tmx_data)
        for _, comps in self.world.query(Transform, DebugRect):
            tr: Transform = comps[Transform]
            dr: DebugRect = comps[DebugRect]
            pygame.draw.rect(surface, dr.color, Rect(int(tr.x), int(tr.y), dr.size[0], dr.size[1]))
