import socket, threading, time
from collections import deque
from game.net import codec, protocol, snapshots
from game.world.world import World
from game.world.actors import hero_factory

TICK_RATE = 30.0
SPAWN_POINTS = [
        (100, 100),
        (200, 100),
        (100, 200),
        (200, 200)
    ]

class GameServer:
    def __init__(self, host="192.168.0.31", port=50000):
        # ECS world
        self.world = World()
        self.clients = {}          # player_id -> (conn, addr)
        self.input_queues = {}     # player_id -> deque of input messages
        self.player_entities = {}  # player_id -> entity id
        self.next_player_id = 1
        self.lock = threading.Lock()
        self.tick = 0
        self.dt = 1.0 / TICK_RATE

        # Networking
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        print(f"Server listening on {self.host}:{self.port}")

    def run(self):
        """Start server: accept clients and run main loop."""
        threading.Thread(target=self.accept_loop, daemon=True).start()
        print("Server loop started")
        self.run_loop()

    # ---- Networking ----
    # Define spawn points (adjust to match your map)

    def accept_loop(self, sock):
        while True:
            conn, addr = sock.accept()
            with self.lock:
                pid = self.next_player_id
                self.next_player_id += 1
                self.clients[pid] = (conn, addr)
                self.input_queues[pid] = deque()

                # Pick spawn location dynamically
                spawn_pos = SPAWN_POINTS[(pid - 1) % len(SPAWN_POINTS)]

                # Spawn hero using your factory
                eid = hero_factory.create(
                    self.world,
                    archetype="hero.knight",  # or your actual archetype key
                    owner_client_id=pid,
                    pos=spawn_pos,
                )
                self.player_entities[pid] = eid

                # Send welcome
                msg = {"type": protocol.MSG_WELCOME, "player_id": pid}
                conn.sendall(codec.encode(msg))
                print(f"Player {pid} connected from {addr}")

            # Start a thread to handle this client
            t = threading.Thread(target=self.handle_client, args=(conn, pid), daemon=True)
            t.start()

    def handle_client(self, conn, pid):
        buffer = ""
        try:
            while True:
                data = conn.recv(4096)
                if not data: break
                buffer += data.decode()
                buffer = self.process_messages(buffer, pid)
        except Exception as e:
            print("Client error:", e)
        finally:
            print("Disconnect", pid)
            self.remove_client(pid)

    def process_messages(self, buffer, pid):
        for msg in codec.decode(buffer):
            if msg.get("type") == protocol.MSG_INPUT:
                with self.lock:
                    self.input_queues[pid].append(msg)
        return buffer

    def remove_client(self, pid):
        with self.lock:
            if pid in self.clients:
                conn, _ = self.clients.pop(pid)
                try: conn.close()
                except: pass
            self.input_queues.pop(pid, None)
            eid = self.player_entities.pop(pid, None)
            if eid:
                self.world.entities.pop(eid, None)

    # ---- Game loop ----
    def run_loop(self):
        while True:
            start = time.time()
            self.tick += 1
            self.apply_inputs()
            self.world.update(self.dt)
            self.broadcast_snapshot()
            elapsed = time.time() - start
            sleep_time = self.dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def apply_inputs(self):
        """Apply queued input messages to the correct player entity."""
        with self.lock:
            from game.world.components import Intent
            for pid, q in self.input_queues.items():
                eid = self.player_entities.get(pid)
                if eid is None: continue
                comps = self.world.entities.get(eid)
                if comps is None: continue

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

    def broadcast_snapshot(self):
        snap = snapshots.make_snapshot(self.world, self.tick)
        data = codec.encode(snap)
        with self.lock:
            for pid, (conn, _) in list(self.clients.items()):
                try:
                    conn.sendall(data)
                except:
                    self.remove_client(pid)


if __name__ == "__main__":
    GameServer().run()
