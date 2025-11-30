# HostDiscovery:
#   - Runs on the host machine.
#   - Listens on DISCOVERY_PORT for "discover" messages.
#   - Replies with "host_ad" that includes host IP and game port.
#
# ClientDiscovery:
#   - Runs on a client in HubScene JOIN mode.
#   - Periodically sends "discover" broadcast packets to DISCOVERY_PORT.
#   - Collects "host_ad" responses into a hosts dict: (ip, port) -> name.

from __future__ import annotations

import socket
import json
from dataclasses import dataclass, field
from typing import Dict, Tuple

DISCOVERY_PORT = 5001
DISCOVERY_MAGIC = "GateCrashers_v1"


@dataclass
class HostDiscovery:
    """Runs on the host so JOIN clients can find it via LAN broadcast."""
    game_port: int = 5000
    name: str = "GateCrashers Host"
    _sock: socket.socket | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Bind to all interfaces on DISCOVERY_PORT
        sock.bind(("", DISCOVERY_PORT))
        sock.setblocking(False)
        self._sock = sock

    def update(self, dt: float) -> None:
        """Pump incoming discovery packets and reply to them."""
        if self._sock is None:
            return

        while True:
            try:
                data, addr = self._sock.recvfrom(4096)
            except BlockingIOError:
                break
            except OSError:
                # Socket probably closed
                return

            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue

            if msg.get("type") != "discover":
                continue
            if msg.get("magic") != DISCOVERY_MAGIC:
                continue

            # Reply with host advertisement
            ip, _port = addr
            response = {
                "type": "host_ad",
                "magic": DISCOVERY_MAGIC,
                "ip": ip,              # client can override with this or use addr[0]
                "port": self.game_port,
                "name": self.name,
            }
            try:
                self._sock.sendto(json.dumps(response).encode("utf-8"), addr)
            except OSError:
                # Ignore send errors
                pass

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None


@dataclass
class ClientDiscovery:
    """
    Runs on a client in JOIN mode to find hosts on the LAN.
    Periodically broadcasts "discover" and listens for "host_ad" replies.
    """
    interval: float = 2.0          # seconds between broadcasts
    _accum: float = field(init=False, default=0.0)
    _sock: socket.socket | None = field(init=False, default=None)
    hosts: Dict[Tuple[str, int], str] = field(init=False, default_factory=dict)
    _broadcast_port: int = field(init=False, default=DISCOVERY_PORT)

    def __post_init__(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Bind to an ephemeral local port so we can receive replies
        sock.bind(("", 0))
        sock.setblocking(False)
        self._sock = sock

    def update(self, dt: float) -> None:
        """Called from HubScene.update(dt) to send broadcasts and read replies."""
        if self._sock is None:
            return

        # Broadcast every interval seconds
        self._accum += dt
        if self._accum >= self.interval:
            self._accum = 0.0
            msg = {
                "type": "discover",
                "magic": DISCOVERY_MAGIC,
            }
            try:
                self._sock.sendto(
                    json.dumps(msg).encode("utf-8"),
                    ("<broadcast>", self._broadcast_port),
                )
            except OSError:
                # Ignore broadcast errors
                pass

        # Read any replies
        while True:
            try:
                data, addr = self._sock.recvfrom(4096)
            except BlockingIOError:
                break
            except OSError:
                return

            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue

            if msg.get("type") != "host_ad":
                continue
            if msg.get("magic") != DISCOVERY_MAGIC:
                continue

            ip = msg.get("ip") or addr[0]
            try:
                port = int(msg.get("port", 5000))
            except ValueError:
                port = 5000
            name = msg.get("name", "Host")

            self.hosts[(ip, port)] = name

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
