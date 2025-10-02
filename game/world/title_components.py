from dataclasses import dataclass, field
from typing import List, Optional, Literal

Role = Literal["host", "client", "singleplayer"]

@dataclass(slots=True)
class TitleMenu:
    title: str = "Dungeon Crawler"
    options: List[str] = field(default_factory=lambda: ["Host", "Join", "Single Player"])
    selected_index: int = 0
    selected_role: Optional[Role] = None