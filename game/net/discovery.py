# AUTHORED BY: Scott Petty, Cole Herzog
# HostDiscovery:
#   - Runs on the host machine.
#   - Listens on DISCOVERY_PORT for "discover" messages.
#   - Replies with "host_ad" that includes HOST LAN IP and game port.
#
# ClientDiscovery:
#   - Runs on a client in HubScene JOIN mode.
#   - Periodically sends "discover" broadcast packets to DISCOVERY_PORT.
#   - Collects "host_ad" responses into a hosts dict: (ip, port) -> name.


from __future__ import annotations

import socket
import json
import threading
import time
from typing import Dict, Tuple

DISCOVERY_PORT = 5001  # separate from game port (5000)
DISCOVERY_MAGIC = "GATECRASHERS_DISCOVERY_V1"


# ---------------------------------------------------------------------------
# HostDiscovery (runs on HOST machine)
# ---------------------------------------------------------------------------

class HostDiscovery:
    """
    Runs on the host machine. Listens for UDP "discover" packets on
    DISCOVERY_PORT and replies with a JSON "host_ad" message containing
    the host's LAN IP + game_port + human-readable name.
    """

    def __init__(self, game_port: int, name: str) -> None:
        self.game_port = int(game_port)
        self.name = name
        self.running = True

        # Single UDP socket bound to all interfaces for discovery
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to all interfaces on the discovery port
        self._sock.bind(("", DISCOVERY_PORT))
        self._sock.settimeout(0.5)

        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()

    def _thread_main(self) -> None:
        while self.running:
            try:
                data, addr = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                # Socket closed
                break

            # Expect a JSON "discover" packet
            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue

            if msg.get("type") != "discover":
                continue
            if msg.get("magic") != DISCOVERY_MAGIC:
                continue

            # Determine the host's LAN IP (not the client's IP)
            host_ip = self._get_lan_ip()

            response = {
                "type": "host_ad",
                "magic": DISCOVERY_MAGIC,
                "ip": host_ip,
                "port": self.game_port,
                "name": self.name,
            }

            try:
                self._sock.sendto(json.dumps(response).encode("utf-8"), addr)
            except OSError:
                # Best effort; ignore errors on send
                pass

    def _get_lan_ip(self) -> str:
        """
        Determine the LAN IP by connecting a dummy UDP socket to a
        likely router address. This does not actually send traffic;
        it just forces the OS to choose an interface.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Any private address will force interface selection; 192.168.1.1
            # is a common default.
            s.connect(("192.168.1.1", 80))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"
        finally:
            s.close()

    def update(self, dt: float) -> None:
        """
        No-op for compatibility with existing HubScene code that calls
        host_discovery.update(dt). All work is done in the thread.
        """
        return

    def close(self) -> None:
        self.running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None


# ---------------------------------------------------------------------------
# ClientDiscovery (runs on JOIN clients)
# ---------------------------------------------------------------------------

class ClientDiscovery:
    """
    Runs on JOIN clients. Periodically broadcasts a "discover" packet
    and collects "host_ad" responses in self.hosts.

    Public state:
        hosts: Dict[(ip, port), name]
    """

    def __init__(self, interval: float = 1.0) -> None:
        self.interval = float(interval)
        self.running = True

        # (ip, port) -> name
        self.hosts: Dict[Tuple[str, int], str] = {}

        # UDP broadcast socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.settimeout(0.3)

        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()

    def _thread_main(self) -> None:
        """
        Loop:
          - Broadcast "discover" packet.
          - For a short window, collect any "host_ad" replies.
          - Sleep until next interval.
        """
        while self.running:
            # 1) Broadcast discover packet
            discover_msg = {
                "type": "discover",
                "magic": DISCOVERY_MAGIC,
            }
            try:
                self._sock.sendto(
                    json.dumps(discover_msg).encode("utf-8"),
                    ("255.255.255.255", DISCOVERY_PORT),
                )
            except OSError:
                # Ignore send errors; we will retry next interval
                pass

            # 2) Collect responses for a short window
            end_time = time.time() + 0.3
            while self.running and time.time() < end_time:
                try:
                    data, addr = self._sock.recvfrom(4096)
                except socket.timeout:
                    break
                except OSError:
                    # Socket closed
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
                except (TypeError, ValueError):
                    port = 5000
                name = msg.get("name", "Host")

                self.hosts[(ip, port)] = name

            # 3) Sleep until next broadcast
            sleep_time = max(0.1, self.interval - 0.3)
            time.sleep(sleep_time)

    def update(self, dt: float) -> None:
        """
        No-op for compatibility with existing HubScene code that calls
        client_discovery.update(dt). All work is done in the thread.
        """
        return

    def close(self) -> None:
        self.running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
