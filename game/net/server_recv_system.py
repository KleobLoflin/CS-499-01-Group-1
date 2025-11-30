# game/net/server_recv_system.py

import socket
from collections import deque

from game.net import config, codec, protocol

class ServerRecvSystem:
    """
    Non-blocking UDP receive system.
    - listens for join
    - listens for input
    - stores packets for apply-input system
    """

    def __init__(self, host: str = config.SERVER_HOST, port: int = config.SERVER_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.sock.setblocking(False)

        # addr -> player_id
        self.addr_to_pid: dict[tuple, int] = {}
        self.next_pid = 1

        # input queue: list of (pid, msg_dict)
        self.input_queue: deque = deque()

        # to let snapshot system broadcast
        self.connected_addrs: set[tuple] = set()

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

            # join
            if mtype == protocol.MSG_JOIN:
                if addr not in self.addr_to_pid and self.next_pid <= config.MAX_PLAYERS:
                    pid = self.next_pid
                    self.next_pid += 1
                    self.addr_to_pid[addr] = pid
                    self.connected_addrs.add(addr)

                    # send accept back
                    resp = {"t": protocol.MSG_ACCEPT, "pid": pid}
                    self.sock.sendto(codec.encode_packet(resp), addr)

                    # NOTE: we do NOT spawn the hero here; a separate system
                    # or a game init step can create the player entity with PlayerTag(pid=pid)
                else:
                    # either already joined or max players
                    pass

            # input
            elif mtype == protocol.MSG_INPUT:
                pid = self.addr_to_pid.get(addr)
                if pid is None:
                    # ignore inputs from unknown clients
                    continue
                # store for apply-input system
                self.input_queue.append((pid, msg))

    # helper for other systems
    def pop_all_inputs(self):
        while self.input_queue:
            yield self.input_queue.popleft()

    def get_socket(self):
        return self.sock

    def get_connected_addrs(self):
        return list(self.connected_addrs)

    def get_player_id_for_addr(self, addr):
        return self.addr_to_pid.get(addr)
