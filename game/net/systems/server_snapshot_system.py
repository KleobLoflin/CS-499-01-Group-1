from game.net import config, codec, snapshots
import time

class ServerSnapshotSystem:
    def __init__(self, recv_system: "ServerRecvSystem"):
        self.recv_system = recv_system
        self.accum = 0.0
        self.tick = 0

    def update(self, world, dt: float):
        self.accum += dt
        # advance authoritative tick at server tick rate
        if self.accum >= (1.0 / config.SERVER_TICK):
            self.tick += 1
            self.accum -= (1.0 / config.SERVER_TICK)

        # but we only SEND at snapshot rate
        # we can keep a separate timer for that
        # for simplicity, reuse another accumulator
        if not hasattr(self, "_snap_accum"):
            self._snap_accum = 0.0
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
                    # if send fails, we could drop the addr from recv_system
                    pass
