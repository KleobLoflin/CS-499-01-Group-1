# Class: Scene

# This is an abstract base class (ABC) for scenes.
# Using this makes python complain early if a concrete scene forgets a required method like update/draw
# possible methods: enter(), exit(), update(dt), draw(surface), handle_event(ev)

from abc import ABC, abstractmethod
from typing import Any

class Scene(ABC):

    # currently all methods are no-ops because they are overwritten by other
    # scene classes that inherit them
    def enter(self) -> None: ...
    def exit(self) -> None: ...

    def handle_event(self, event: Any) -> None: ...
    @abstractmethod
    def update(self, dt: float) -> None: ...
    @abstractmethod
    def draw(self, surface) -> None: ...