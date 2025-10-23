# Class: SceneManager

# controls which scene is active and forwards events/update/draw to it
# possible fields: stack: list[Scene]
# possible methods: set(scene), push(scene), pop(), update(dt), draw(surface), handle_event(ev)
# This class controls switching scenes and keeps it decoupled from game logic.
# Scenes are hot-swappable (Menu, Hub, Dungeon, ect...)

from __future__ import annotations
from typing import Optional
from game.scenes.base import Scene

class SceneManager:
    def __init__(self) -> None:
        # no scene yet at startup. Optional[Scene] means "Scene or None"
        self._active: Optional[Scene] = None

    # sets the active scene.
    # It exits any active scene and enters the new one
    def set(self, scene: Scene) -> None:
        if self._active:
            self._active.exit()
        self._active = scene
        self._active.enter()

    # forwards input events (keyboard/mouse) to the active scene
    def handle_event(self, event) -> None:
        if self._active:
            self._active.handle_event(event)

    # runs one fixed simulation step on the active scene
    def update(self, dt: float) -> None:
        if self._active:
            self._active.update(dt)

    # asks the active scene to render itself
    def draw(self, surface) -> None:
        if self._active:
            self._active.draw(surface)
