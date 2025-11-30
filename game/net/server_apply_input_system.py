# game/net/server_apply_input_system.py

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
                intent = Intent()
                world.add(eid, intent)

            # map network fields to your Intent
            intent.move_x = float(msg.get("mx", 0.0))
            intent.move_y = float(msg.get("my", 0.0))
            intent.dash = bool(msg.get("dash", False))
            intent.basic_atk = bool(msg.get("basic", False))
            intent.basic_atk_held = bool(msg.get("basic_held", False))
            intent.special_atk = bool(msg.get("special", False))

            facing = msg.get("facing")
            if facing:
                intent.facing = facing
