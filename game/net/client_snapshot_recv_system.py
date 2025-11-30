# game/net/client_snapshot_recv_system.py

import socket
from typing import Optional

from game.net import config, codec, protocol, snapshots

class ClientSnapshotRecvSystem:
    """
    Receives MSG_ACCEPT (pid assignment) and MSG_SNAPSHOT from the server.
    Applies snapshots to the local world.
    """

    def __init__(
        self,
        bind_port: int = 0,
        sock: Optional[socket.socket] = None,
    ):
        # support sharing a UDP socket with the input send system
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(("0.0.0.0", bind_port))
            self.sock.setblocking(False)
        else:
            self.sock = sock

        self.local_pid: int | None = None

    def set_local_pid(self, pid: int):
        self.local_pid = pid

    def get_socket(self):
        return self.sock

    def update(self, world, dt: float):
        from game.net.client_input_send_system import ClientInputSendSystem

        while True:
            try:
                data, addr = self.sock.recvfrom(config.MAX_UDP_SIZE)
            except BlockingIOError:
                break

            msg = codec.decode_packet(data)
            if not msg:
                continue

            mtype = msg.get("t")
            if mtype == protocol.MSG_ACCEPT:
                # server told us our pid
                self.local_pid = msg.get("pid")

            elif mtype == protocol.MSG_SNAPSHOT:
                snapshots.apply_snapshot(world, msg, self.local_pid)
