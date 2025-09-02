from typing import Dict, List, Type, Iterator, Tuple, Any

class World:
    """
    ECS-lite container: entities are dicts {ComponentType: instance}.
    Systems are objects with update(world, dt).
    """
    def __init__(self) -> None:
        self.entities: Dict[int, Dict[Type, Any]] = {}
        self.systems: List[Any] = []
        self._next_id = 1

    # ---- entity & components ----
    def new_entity(self) -> int:
        eid = self._next_id
        self._next_id += 1
        self.entities[eid] = {}
        return eid

    def add(self, eid: int, comp: Any) -> None:
        self.entities[eid][type(comp)] = comp

    def get(self, eid: int, comp_type: Type) -> Any:
        return self.entities[eid].get(comp_type)

    def query(self, *comp_types: Type) -> Iterator[Tuple[int, Dict[Type, Any]]]:
        for eid, comps in self.entities.items():
            if all(ct in comps for ct in comp_types):
                yield eid, comps

    # ---- tick ----
    def update(self, dt: float) -> None:
        for sys in self.systems:
            sys.update(self, dt)
