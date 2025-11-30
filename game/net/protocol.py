# game/net/protocol.py
# Message type ids for UDP packets

# client -> server
MSG_JOIN = 1        # client wants to join
MSG_INPUT = 3       # client input (authoritative server will apply)

# server -> client
MSG_ACCEPT = 2      # server assigns player id
MSG_SNAPSHOT = 4    # server snapshot of world
