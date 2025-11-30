# game/net/client_input_send_system.py

import socket
from typing import Optional

from game.net import config, codec, protocol
from game.world.components import Intent

class ClientInputSendSystem:
    """
    Periodically sends the local player's Intent to the server over UDP.
    Also handles sending a one-time MSG_JOIN on first update.
    """

    def __init__(
        self,
        server_addr: tuple[str, int] = ("127.0.0.1", config.SERVER_PORT),
        local_player_eid: int | None = None,
        sock: Optional[socket.socket] = None,
    ):
        # server address (host, port)
        self.server_addr = server_addr

        # allow sharing a socket with the snapshot recv system
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setblocking(False)
        else:
            self.sock = sock

        self.local_player_eid = local_player_eid
        self.send_accum = 0.0

        self.assigned_pid: int | None = None  # filled when we get MSG_ACCEPT (via recv system)
        self._join_sent = False

    def set_local_player(self, eid: int):
        self.local_player_eid = eid

    def set_assigned_pid(self, pid: int):
        self.assigned_pid = pid

    def _send_join_if_needed(self):
        if self._join_sent:
            return
        msg = {"t": protocol.MSG_JOIN}
        try:
            self.sock.sendto(codec.encode_packet(msg), self.server_addr)
            self._join_sent = True
        except OSError:
            # if it fails, we'll try again next update
            pass

    def update(self, world, dt: float):
        # make sure we've tried to join
        self._send_join_if_needed()

        self.send_accum += dt
        if self.send_accum < (1.0 / config.CLIENT_SEND_RATE):
            return
        self.send_accum = 0.0

        if self.local_player_eid is None:
            return

        comps = world.entities.get(self.local_player_eid)
        if comps is None:
            return

        intent: Intent | None = comps.get(Intent)
        if intent is None:
            return

        msg = {
            "t": protocol.MSG_INPUT,
            "mx": intent.move_x,
            "my": intent.move_y,
            "dash": intent.dash,
            "basic": intent.basic_atk,
            "basic_held": intent.basic_atk_held,
            "special": intent.special_atk,
            "facing": intent.facing,
        }

        try:
            self.sock.sendto(codec.encode_packet(msg), self.server_addr)
        except OSError:
            # ignore send errors for now
            pass
