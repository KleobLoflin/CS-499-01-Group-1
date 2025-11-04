from game.world.components import Intent

class ServerApplyInputSystem:
    """
    Applies client inputs (already received by ServerRecvSystem)
    to the corresponding player entities.
    """

    def __init__(self, recv_system: "ServerRecvSystem", player_map: dict[int, int]):
        """
        recv_system: the instance of ServerRecvSystem so we can read its queue
        player_map: pid -> eid (you can keep this dict in your server bootstrap)
        """
        self.recv_system = recv_system
        self.player_map = player_map

    def update(self, world, dt: float):
        for pid, msg in self.recv_system.pop_all_inputs():
            eid = self.player_map.get(pid)
            if eid is None:
                continue

            comps = world.entities.get(eid)
            if comps is None:
                continue

            intent = comps.get(Intent)
            if intent is None:
                intent = Intent(move_x=0.0, move_y=0.0, dash_x=0.0, dash_y=0.0)
                world.add(eid, intent)

            # map network fields to your intent
            intent.move_x = msg.get("mx", msg.get("move_x", 0.0))
            intent.move_y = msg.get("my", msg.get("move_y", 0.0))
            intent.dash_x = msg.get("dx", msg.get("dash_x", 0.0))
            intent.dash_y = msg.get("dy", msg.get("dash_y", 0.0))
