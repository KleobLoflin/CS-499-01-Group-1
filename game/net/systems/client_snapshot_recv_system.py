import socket
from game.net import config, codec, protocol, snapshots

class ClientSnapshotRecvSystem:
    def __init__(self, bind_port: int = 0):
        # bind_port=0 lets OS pick a port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", bind_port))
        self.sock.setblocking(False)

        self.local_pid = None

    def set_local_pid(self, pid: int):
        self.local_pid = pid

    def update(self, world, dt: float):
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
