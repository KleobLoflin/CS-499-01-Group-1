# Non-blocking UDP server wrapper used by the host.

from __future__ import annotations

import socket
from typing import Dict, Tuple, List, Any

from game.net.codec import encode_message, decode_message

Address = Tuple[str, int]


class NetServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 5000,
                 buffer_size: int = 65535) -> None:
        self.address: Address = (host, port)
        self.buffer_size = buffer_size

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind(self.address)
        self._sock = sock

        # Maps: peer_id -> address, and reverse.
        self.peer_to_addr: Dict[str, Address] = {}
        self.addr_to_peer: Dict[Address, str] = {}

    # I/O ##################################################################

    # non-blocking recieve loop. Returns a list of (addr, message_dict).
    def recv_all(self) -> List[Tuple[Address, dict]]:
        messages: List[Tuple[Address, dict]] = []
        while True:
            try:
                data, addr = self._sock.recvfrom(self.buffer_size)
            except BlockingIOError:
                break
            except OSError:
                break

            try:
                msg = decode_message(data)
            except Exception:
                continue

            messages.append((addr, msg))

        return messages

    def send_raw(self, addr: Address, message: dict) -> None:
        try:
            self._sock.sendto(encode_message(message), addr)
        except OSError:
            # Ignore send errors. socket might be closed.
            pass

    def send_to_peer(self, peer_id: str, message: dict) -> None:
        addr = self.peer_to_addr.get(peer_id)
        if addr is None:
            return
        self.send_raw(addr, message)

    def broadcast(self, message: dict) -> None:
        for addr in list(self.peer_to_addr.values()):
            self.send_raw(addr, message)

    # bookkeeping ##########################################################

    def register_peer(self, peer_id: str, addr: Address) -> None:
        self.peer_to_addr[peer_id] = addr
        self.addr_to_peer[addr] = peer_id

    def unregister_peer(self, peer_id: str) -> None:
        addr = self.peer_to_addr.pop(peer_id, None)
        if addr is not None:
            self.addr_to_peer.pop(addr, None)

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass
