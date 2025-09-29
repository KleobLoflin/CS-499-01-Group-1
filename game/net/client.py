# client.py
import socket
import threading
import json
from collections import deque
from game.net import codec, protocol, snapshots
from game.world.components import Intent

class GameClient:
    def __init__(self, host="127.0.0.1", port=50000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_buffer = ""
        self.snapshot_queue = deque()
        self.player_id = None
        self.connected = False

    def connect(self):
        self.sock.connect((self.host, self.port))
        self.connected = True
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def receive_loop(self):
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                self.recv_buffer += data.decode()
                for msg in codec.decode(self.recv_buffer):
                    self.handle_message(msg)
                self.recv_buffer = ""
            except Exception as e:
                print("Client receive error:", e)
                break

    def handle_message(self, msg):
        t = msg.get("type")
        if t == protocol.MSG_WELCOME:
            self.player_id = msg["player_id"]
            print("Connected as player", self.player_id)
        elif t == protocol.MSG_SNAPSHOT:
            self.snapshot_queue.append(msg)

    def send_input(self, intent: Intent, tick: int):
        if not self.connected:
            return #skip until connected
        msg = {
            "type": protocol.MSG_INPUT,
            "tick": tick,
            "move_x": intent.move_x,
            "move_y": intent.move_y,
            "dash_x": intent.dash_x,
            "dash_y": intent.dash_y,
        }
        try:
            self.sock.sendall(codec.encode(msg))
        except Exception as e:
            print(f"[Client 1 error]: {e}")
            self.connected = False

    def poll_snapshot(self):
        """Return the latest snapshot from the queue, if any."""
        if self.snapshot_queue:
            return self.snapshot_queue.popleft()
        return None
