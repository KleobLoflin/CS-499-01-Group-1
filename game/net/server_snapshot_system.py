# game/net/server_snapshot_system.py

from game.net import config, codec, snapshots
import time

class ServerSnapshotSystem:
    """
    Periodically builds a world snapshot and broadcasts it to all
    connected clients known by ServerRecvSystem.
    """

    def __init__(self, recv_system: "ServerRecvSystem"):
        self.recv_system = recv_system
        self.accum = 0.0
        self.tick = 0
        self._snap_accum = 0.0

    def update(self, world, dt: float):
        # advance authoritative tick at server tick rate
        self.accum += dt
        while self.accum >= (1.0 / config.SERVER_TICK):
            self.tick += 1
            self.accum -= (1.0 / config.SERVER_TICK)

        # snapshot send rate
        self._snap_accum += dt
        if self._snap_accum >= (1.0 / config.SERVER_SNAPSHOT_RATE):
            self._snap_accum -= (1.0 / config.SERVER_SNAPSHOT_RATE)

            snap = snapshots.make_snapshot(world, self.tick)
            data = codec.encode_packet(snap)

            sock = self.recv_system.get_socket()
            for addr in self.recv_system.get_connected_addrs():
                try:
                    sock.sendto(data, addr)
                except OSError:
                    # if send fails, we could drop the addr from recv_system later
                    pass
