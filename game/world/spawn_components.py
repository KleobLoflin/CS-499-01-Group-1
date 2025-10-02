from dataclasses import dataclass
from typing import Dict, Any

@dataclass(slots=True)
class MapLoaded:
    map_id: str
    blueprint: Dict[str, Any]