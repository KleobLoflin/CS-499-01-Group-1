# server.py — authoritative game server for multiplayer dungeon
#
# Manages world state, receives client inputs, applies them, and broadcasts snapshots.

import socket
import threading
import time
from collections import deque

from game.net import codec, protocol, snapshots
from game.world.world import World
from game.world.actors import hero_factory
from game.world.actors.blueprint_index import load as load_blueprints

# Load hero/enemy blueprints
load_blueprints("data/blueprints/heroes.json", "data/blueprints/enemies.json")

TICK_RATE = 30.0
SPAWN_POINTS = [
    (100, 100),
    (200, 100),
    (100, 200),
    (200, 200)
]

class GameServer:
    def __init__(self, host="0.0.0.0", port=50000):
        self.world = World()

        # Networking
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        print(f"[SERVER] Listening on {self.host}:{self.port}")

        # Player management
        self.clients: dict[int, tuple[socket.socket, tuple]] = {}
        self.input_queues: dict[int, deque] = {}
        self.player_entities: dict[int, int] = {}
        self.next_player_id = 1
        self.lock = threading.Lock()

        # Timing
        self.tick = 0
        self.dt = 1.0 / TICK_RATE
        self.running = True

    # ───────────────────────────────────────────────
    # SERVER LOOP
    # ───────────────────────────────────────────────
    def run(self):
        """Start server: accept clients and run main loop."""
        threading.Thread(target=self._accept_loop, daemon=True).start()
        print("[SERVER] Main loop started")
        self._main_loop()

    def _main_loop(self):
        """Tick loop for world update + snapshot broadcast."""
        while self.running:
            start = time.time()
            self.tick += 1

            # Apply all queued inputs
            self._apply_inputs()

            # Update world
            self.world.update(self.dt)

            # Broadcast world snapshot
            self._broadcast_snapshot()

            # Maintain tick rate
            elapsed = time.time() - start
            sleep_time = self.dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ───────────────────────────────────────────────
    # CLIENT MANAGEMENT
    # ───────────────────────────────────────────────
    def _accept_loop(self):
        while self.running:
            conn, addr = self.sock.accept()
            with self.lock:
                pid = self.next_player_id
                self.next_player_id += 1
                self.clients[pid] = (conn, addr)
                self.input_queues[pid] = deque()

                # Pick spawn location
                spawn_pos = SPAWN_POINTS[(pid - 1) % len(SPAWN_POINTS)]

                # Spawn hero
                try:
                    eid = hero_factory.create(
                        self.world,
                        archetype="knight",
                        owner_client_id=pid,
                        pos=spawn_pos
                    )
                    self.player_entities[pid] = eid
                except KeyError as e:
                    print(f"[ERROR] Failed to spawn hero for player {pid}: {e}")
                    conn.close()
                    continue

                # Send welcome message
                msg = {"type": protocol.MSG_WELCOME, "player_id": pid}
                conn.sendall(codec.encode(msg))
                print(f"[SERVER] Player {pid} connected from {addr}")

            # Start client thread
            threading.Thread(target=self._client_loop, args=(conn, pid), daemon=True).start()

    def _client_loop(self, conn: socket.socket, pid: int):
        buffer = ""
        try:
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break
                buffer += data.decode()
                buffer = self._process_messages(buffer, pid)
        except Exception as e:
            print(f"[SERVER] Client {pid} error: {e}")
        finally:
            print(f"[SERVER] Player {pid} disconnected")
            self._remove_client(pid)

    def _process_messages(self, buffer: str, pid: int) -> str:
        """Decode messages and queue input events."""
        for msg in codec.decode(buffer):
            if msg.get("type") == protocol.MSG_INPUT:
                with self.lock:
                    self.input_queues[pid].append(msg)
        return buffer

    def _remove_client(self, pid: int):
        """Cleanly remove a client and its entity from the world."""
        with self.lock:
            if pid in self.clients:
                conn, _ = self.clients.pop(pid)
                try:
                    conn.close()
                except:
                    pass
            self.input_queues.pop(pid, None)
            eid = self.player_entities.pop(pid, None)
            if eid:
                self.world.entities.pop(eid, None)

    # ───────────────────────────────────────────────
    # INPUT & SNAPSHOT
    # ───────────────────────────────────────────────
    def _apply_inputs(self):
        """Apply queued client inputs to player entities."""
        from game.world.components import Intent

        with self.lock:
            for pid, q in self.input_queues.items():
                eid = self.player_entities.get(pid)
                if eid is None:
                    continue

                comps = self.world.entities.get(eid)
                if comps is None:
                    continue

                intent = comps.get(Intent)
                if intent is None:
                    intent = Intent(move_x=0.0, move_y=0.0, dash_x=0.0, dash_y=0.0)
                    self.world.add(eid, intent)

                while q:
                    msg = q.popleft()
                    intent.move_x = msg.get("move_x", 0.0)
                    intent.move_y = msg.get("move_y", 0.0)
                    intent.dash_x = msg.get("dash_x", 0.0)
                    intent.dash_y = msg.get("dash_y", 0.0)

    def _broadcast_snapshot(self):
        """Send the latest world snapshot to all clients."""
        snap = snapshots.make_snapshot(self.world, self.tick)
        data = codec.encode(snap)

        with self.lock:
            for pid, (conn, _) in list(self.clients.items()):
                try:
                    conn.sendall(data)
                except Exception:
                    self._remove_client(pid)

# ───────────────────────────────────────────────
# ENTRY POINT
# ───────────────────────────────────────────────
if __name__ == "__main__":
    server = GameServer()
    server.run()
