# class: World

# minimal ECS-lite container:
# - Entity = integer ID with a dict of component instances
# - System = object with update(world, dt)
# world.update runs systems in the registered order


from typing import Dict, List, Type, Iterator, Tuple, Any

class World:
    def __init__(self) -> None:
        self.entities: Dict[int, Dict[Type, Any]] = {}      # id -> {CompType: comp}
        self.systems: List[Any] = []                        # ordered list of systems
        self._next_id = 1                                   # next integer id to be given
        self._to_delete: List[int] = []

    # entity & component management #########################################################

    # build new entity
    def new_entity(self) -> int:
        eid = self._next_id # entity id
        self._next_id += 1
        self.entities[eid] = {}
        return eid

    # add a component instance to an entity
    def add(self, eid: int, comp: Any) -> None:
        self.entities[eid][type(comp)] = comp

    # get a component instance from an entity
    def get(self, eid: int, comp_type: Type) -> Any:
        comps = self.entities.get(eid)
        if comps is None:
            return None
        return comps.get(comp_type)
    
    # return the component dict for the entity
    def components_of(self, eid: int) -> Dict[Type, Any]:
        return self.entities.setdefault(eid, {})

    # iterates through entities that have all of the requested component types
    # yields (entity_id, component_dict) pairs 
    def query(self, *comp_types: Type) -> Iterator[Tuple[int, Dict[Type, Any]]]:
        for eid, comps in self.entities.items():
            if all(ct in comps for ct in comp_types):
                yield eid, comps

    # simulation tick ###############################################################
    # run each system once. order matters in the systems list
    def update(self, dt: float) -> None:
        for sys in self.systems:
            sys.update(self, dt)
        self.cleanup_deleted()

      # completely remove an entity and all its components
    def delete_entity(self, eid: int) -> None:
        #"""Removes the given entity and all of its components from the world."""
        if eid in self.entities:
            del self.entities[eid]


    def cleanup_deleted(self) -> None:
        """Remove all entities queued for deletion."""
        for eid in self._to_delete:
            self.entities.pop(eid, None)
        self._to_delete.clear()