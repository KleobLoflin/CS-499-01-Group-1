# game/net/config.py

# Where the authoritative server binds
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 50000

# Authoritative sim rate (server world tick)
SERVER_TICK = 30.0  # 30 Hz

# How often we send snapshots to clients
SERVER_SNAPSHOT_RATE = 20.0  # 20 Hz

# How often clients send inputs to the server
CLIENT_SEND_RATE = 20.0  # 20 Hz

MAX_PLAYERS = 5
MAX_UDP_SIZE = 4096
