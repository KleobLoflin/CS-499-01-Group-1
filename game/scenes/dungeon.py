# Class DungeonScene(Scene)

# actual gameplay scene
# possible fields: world, net, hud, camera, local_player_id...
# possible methods: update(dt): send local inputs -> poll snapshots ->
# client prediction/reconciliation -> world.update(dt).
# in draw(): render world -> HUD.

# owns a world, registers systems in order, and draws entities

from game.scenes.base import Scene
from game.scenes.base import Scene
import pygame
import pytmx
from pygame import Surface
from game.core.config import Config
from game.core import resources
from game.world.world import World
from game.world.components import Transform, Intent, Sprite, AnimationState, Facing
from game.world.systems.input import InputSystem
from game.world.systems.movement import MovementSystem
from game.world.systems.ai import EnemyAISystem
from game.world.systems.collision import CollisionSystem
from game.world.systems.presentation_mapper import PresentationMapperSystem
from game.world.systems.animation import AnimationSystem
from game.world.systems.room import Room
from game.net.client import GameClient
from game.net import snapshots
from game.world.actors.hero_factory import create as create_hero
from game.world.actors.enemy_factory import create as create_enemy



class DungeonScene(Scene):
    def __init__(self) -> None:
        self.world = World()
        self.player_id: int | None = None
        self.net = GameClient()
        self.world.tick = 0
        self.input_system = None

        # Initialize Tiled map
        self.world.tmx_data = pytmx.load_pygame("assets/maps/testmap.tmx")

    def enter(self) -> None:
        # Connect to server
        self.net.connect()

        # Spawn player hero entity first
        self.player_id = create_hero(
            self.world,
            archetype="knight",
            owner_client_id=None,
            pos=(Config.WINDOW_W / 2 - 16, Config.WINDOW_H / 2 - 16)
        )

        # Spawn a test enemy
        self.chaser_1_id = create_enemy(
            self.world,
            kind="chort",
            pos=(100, 100),
            params={"target_id": self.player_id, "agro_range": 200}
        )

        # Initialize InputSystem with the valid player_id
        input_system = InputSystem(player_id=self.player_id)

        # Register systems in order
        self.world.systems = [
            input_system,
            EnemyAISystem(),
            MovementSystem(),
            CollisionSystem(self.player_id),  # pass the actual player_id
            PresentationMapperSystem(),
            AnimationSystem(),
        ]

    def handle_event(self, event) -> None:
        # Pass events to input system
        if self.input_system:
            self.input_system.handle_event(event)

    def update(self, dt: float) -> None:
        # --- 1. Poll latest snapshot from server ---
        snapshot_data = self.net.poll_snapshot()
        if snapshot_data:
            # Assign player_id on first snapshot
            if self.player_id is None and "heroes" in snapshot_data:
                for h in snapshot_data["heroes"]:
                    if h["owner"] == self.net.player_id:
                        self.player_id = h["owner"]
                        self.input_system.player_id = self.player_id
                        # Update systems that need player_id
                        for sys in self.world.systems:
                            if hasattr(sys, "player_id"):
                                sys.player_id = self.player_id
                        break
            # Apply snapshot to local ECS world
            snapshots.apply_snapshot(self.world, snapshot_data)

        # --- 2. Send local input to server ---
        if self.player_id is not None:
            intent = self.world.get(self.player_id, Intent)
            if intent:
                self.net.send_input(intent, tick=self.world.tick)

        # --- 3. Update ECS world ---
        self.world.update(dt)

        # --- 4. Increment tick counter ---
        self.world.tick += 1

    def draw(self, surface: Surface) -> None:
        # Clear screen
        surface.fill(Config.BG_COLOR)

        # Draw map
        Room.draw_map(surface, self.world.tmx_data)

        # Render entities
        render_list = []
        for _, comps in self.world.query(Transform, Sprite, AnimationState, Facing):
            tr = comps[Transform]
            spr = comps[Sprite]
            anim = comps[AnimationState]
            face = comps[Facing]

            frames, _, _, mirror_x, origin = resources.clip_info(spr.atlas_id, anim.clip)
            if not frames:
                continue

            img = frames[anim.frame]
            if face.direction < 0 and mirror_x:
                img = pygame.transform.flip(img, True, False)

            pos = (int(tr.x - origin[0]), int(tr.y - origin[1]))
            render_list.append((spr.z, img, pos))

        # Sort by z-index and draw
        render_list.sort(key=lambda t: t[0])
        for _, img, pos in render_list:
            surface.blit(img, pos)
