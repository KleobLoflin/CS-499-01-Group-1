# AUTHORED BY: Scott Petty, Cole Herzog
# Non-blocking UDP client wrapper used by remote peers.

from __future__ import annotations

import socket
from typing import List, Tuple, Dict, Any

from game.net.codec import encode_message, decode_message

Address = Tuple[str, int]


class NetClient:
    def __init__(self, host: str, port: int,
                 local_port: int = 0, buffer_size: int = 65535) -> None:
        self.remote: Address = (host, port)
        self.buffer_size = buffer_size

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind(("0.0.0.0", local_port))
        self._sock = sock

    # I/O

    def send(self, message: Dict[str, Any]) -> None:
        try:
            self._sock.sendto(encode_message(message), self.remote)
        except OSError:
            pass

    def recv_all(self) -> List[dict]:
        messages: List[dict] = []
        while True:
            try:
                data, _addr = self._sock.recvfrom(self.buffer_size)
            except BlockingIOError:
                break
            except OSError:
                break

            try:
                msg = decode_message(data)
            except Exception:
                continue

            messages.append(msg)

        return messages

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass
