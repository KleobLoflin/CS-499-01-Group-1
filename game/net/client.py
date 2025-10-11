# client.py — network client for multiplayer dungeon
#
# Connects to GameServer (server.py), sends player inputs, and applies world snapshots.
# For now, it's safe to leave unconnected — DungeonScene("single") still works fine.

import socket
import threading
import time
from collections import deque

from game.net import codec, protocol, snapshots

# Optional future: integrate into DungeonScene via self.net
# Example:
#     self.net = GameClient("127.0.0.1", 50000)
#     self.net.start()


class GameClient:
    def __init__(self, host="127.0.0.1", port=50000):
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None
        self.recv_thread: threading.Thread | None = None

        self.buffer = ""
        self.running = False
        self.player_id: int | None = None

        # message queues
        self.outgoing_inputs = deque()   # messages waiting to be sent to server
        self.snapshots = deque(maxlen=4) # latest few world snapshots

        # thread lock
        self._lock = threading.Lock()

    # ───────────────────────────────────────────────
    # CONNECTION MANAGEMENT
    # ───────────────────────────────────────────────
    def connect(self) -> bool:
        """Try connecting to the server and wait for welcome message."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.running = True

            # start receive thread
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()

            print(f"[CLIENT] Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[CLIENT ERROR] Could not connect: {e}")
            self.running = False
            return False

    def close(self):
        """Close socket cleanly."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        print("[CLIENT] Disconnected")

    # ───────────────────────────────────────────────
    # NETWORK LOOPS
    # ───────────────────────────────────────────────
    def _recv_loop(self):
        """Receive data from the server and decode messages."""
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                self.buffer += data.decode()
                self.buffer = self._process_messages(self.buffer)
            except Exception as e:
                print(f"[CLIENT recv_loop ERROR]: {e}")
                break

        self.close()

    def _process_messages(self, buffer: str) -> str:
        """Process decoded messages from the server."""
        for msg in codec.decode(buffer):
            mtype = msg.get("type")

            if mtype == protocol.MSG_WELCOME:
                self.player_id = msg.get("player_id")
                print(f"[CLIENT] Received welcome, assigned ID={self.player_id}")

            elif mtype == protocol.MSG_SNAPSHOT:
                with self._lock:
                    self.snapshots.append(msg)

            # future: handle chat, state sync, disconnect, etc.
        return buffer

    # ───────────────────────────────────────────────
    # INPUT & SNAPSHOT INTERFACE
    # ───────────────────────────────────────────────
    def send_input(self, move_x, move_y, dash_x=0.0, dash_y=0.0):
        """Queue a player input message to send."""
        msg = {
            "type": protocol.MSG_INPUT,
            "move_x": move_x,
            "move_y": move_y,
            "dash_x": dash_x,
            "dash_y": dash_y,
        }
        self.outgoing_inputs.append(msg)

    def poll_snapshot(self):
        """Pop the newest snapshot (if any)."""
        with self._lock:
            if self.snapshots:
                return self.snapshots.pop()
        return None

    def update(self):
        """Send queued inputs to the server once per tick."""
        if not self.running or not self.sock:
            return
        try:
            while self.outgoing_inputs:
                msg = self.outgoing_inputs.popleft()
                self.sock.sendall(codec.encode(msg))
        except Exception as e:
            print(f"[CLIENT SEND ERROR]: {e}")
            self.close()

    # ───────────────────────────────────────────────
    # STATIC HELPER
    # ───────────────────────────────────────────────
    @staticmethod
    def integrate_snapshot(world, snapshot):
        """Apply snapshot to the ECS world (client-authoritative state correction)."""
        if not snapshot:
            return
        snapshots.apply_snapshot(world, snapshot)
