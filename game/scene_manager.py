# Class: SceneManager

# controls which scene is active (Menu -> Hub -> Dungeon)
# possible fields: stack: list[Scene]
# possible methods: set(scene), push(scene), pop(), update(dt), draw(surface), handle_event(ev)
# This class controls switching scenes and keeps it decoupled from game logic

from __future__ import annotations
from typing import Optional
from game.scenes.base import Scene

class SceneManager:
    def __init__(self) -> None:
        self._active: Optional[Scene] = None

    def set(self, scene: Scene) -> None:
        if self._active:
            self._active.exit()
        self._active = scene
        self._active.enter()

    def handle_event(self, event) -> None:
        if self._active:
            self._active.handle_event(event)

    def update(self, dt: float) -> None:
        if self._active:
            self._active.update(dt)

    def draw(self, surface) -> None:
        if self._active:
            self._active.draw(surface)
