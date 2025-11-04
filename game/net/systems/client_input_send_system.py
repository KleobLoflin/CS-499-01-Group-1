import socket
from game.net import config, codec, protocol

class ClientInputSendSystem:
    def __init__(self, server_addr=("127.0.0.1", config.SERVER_PORT), local_player_eid: int | None = None):
        self.server_addr = server_addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

        self.local_player_eid = local_player_eid
        self.send_accum = 0.0
        self.assigned_pid = None  # filled when we get MSG_ACCEPT

    def set_local_player(self, eid: int):
        self.local_player_eid = eid

    def set_assigned_pid(self, pid: int):
        self.assigned_pid = pid

    def update(self, world, dt: float):
        self.send_accum += dt
        if self.send_accum < (1.0 / config.CLIENT_SEND_RATE):
            return
        self.send_accum = 0.0

        if self.local_player_eid is None:
            return

        comps = world.entities.get(self.local_player_eid)
        if comps is None:
            return

        # we assume your local input system has already written to Intent
        from game.world.components import Intent
        intent = comps.get(Intent)
        if intent is None:
            return

        msg = {
            "t": protocol.MSG_INPUT,
            # might be None right now; server can also map by addr
            "mx": intent.move_x,
            "my": intent.move_y,
            "dx": getattr(intent, "dash_x", 0.0),
            "dy": getattr(intent, "dash_y", 0.0),
        }

        try:
            self.sock.sendto(codec.encode_packet(msg), self.server_addr)
        except OSError:
            pass
