# Class: Scene

# This is the base interface for all scenes
# possible methods: enter(), exit(), update(dt), draw(surface), handle_event(ev)
# makes it where each scene plugs into the game-loop cleanly

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class Scene(ABC):
    """Lifecycle contract every scene must implement."""
    def enter(self) -> None: ...
    def exit(self) -> None: ...

    def handle_event(self, event: Any) -> None: ...
    @abstractmethod
    def update(self, dt: float) -> None: ...
    @abstractmethod
    def draw(self, surface) -> None: ...