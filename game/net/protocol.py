# AUTHORED BY: Scott Petty, Cole Herzog
# description of the wire protocol and message types.

from __future__ import annotations
from typing import Literal

PROTOCOL_VERSION = 1

MessageType = Literal[
    "hello",        # client -> host: initial handshake
    "welcome",      # host  -> client: assign peer_id
    "join_denied",  # host  -> client: lobby full / version mismatch
    "input",        # client -> host: input snapshot
    "snapshot",     # host  -> client: world snapshot
    "start_game",   # host  -> clients: transition hub -> dungeon
    "lobby_update", # client -> host (hero/ready change)
    "lobby_state",  # host -> clients (lobby slots)
    "ping",         # ping
    "pong",         # pong
    "disconnect",   # either direction: polite disconnect
]

MSG_HELLO       = "hello"
MSG_WELCOME     = "welcome"
MSG_JOIN_DENY   = "join_denied"
MSG_INPUT       = "input"
MSG_SNAPSHOT    = "snapshot"
MSG_START_GAME  = "start_game"
MSG_LOBBY_UPDATE = "lobby_update"
MSG_LOBBY_STATE = "lobby_state"
MSG_PING        = "ping"
MSG_PONG        = "pong"
MSG_DISCONNECT  = "disconnect"
