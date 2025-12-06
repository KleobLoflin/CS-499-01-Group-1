# AUTHORED BY: Scott Petty, Cole Herzog

# game/world/systems/net_host.py
#
# NetHostSystem:
#   - Runs ONLY on the host (NetIdentity.role == "HOST").
#   - Handles:
#       * Handshake (hello/welcome).
#       * Receiving remote input and applying it to Owner(peer) entities.
#       * Broadcasting world snapshots at a fixed rate.
#       * Being aware of up to max_clients (4 clients -> 5 total players).

from __future__ import annotations

from typing import Any, Dict, Tuple

from game.world.components import (
    NetIdentity,
    NetHostState,
    Owner,
    PlayerTag,
    Intent,
    InputState,
)
from game.net.server import NetServer
from game.net.protocol import (
    PROTOCOL_VERSION,
    MSG_HELLO,
    MSG_WELCOME,
    MSG_JOIN_DENY,
    MSG_INPUT,
    MSG_SNAPSHOT,
    MSG_PING,
    MSG_PONG,
    MSG_DISCONNECT,
)
from game.net.snapshots import build_world_snapshot

Address = Tuple[str, int]

class NetHostSystem:
    def update(self, world, dt: float) -> None:
        # Locate network singleton
        net_id: NetIdentity | None = None
        host: NetHostState | None = None

        for _eid, comps in world.query(NetIdentity, NetHostState):
            net_id = comps[NetIdentity]
            host = comps[NetHostState]
            break

        if net_id is None or host is None:
            return
        if net_id.role != "HOST":
            return
        if host.server is None:
            return

        server: NetServer = host.server

        # Handle incoming messages
        for addr, msg in server.recv_all():
            self._handle_message(world, server, host, addr, msg)

        # Tick + send snapshots at a fixed interval
        host.accumulator += dt
        while host.accumulator >= host.send_interval:
            host.accumulator -= host.send_interval
            host.tick += 1

            snapshot_payload = build_world_snapshot(world, host.tick)
            packet: Dict[str, Any] = {
                "type": MSG_SNAPSHOT,
                "protocol": PROTOCOL_VERSION,
                **snapshot_payload,
            }
            server.broadcast(packet)

    # internals ################################################################

    def _handle_message(
        self,
        world,
        server: NetServer,
        host: NetHostState,
        addr: Address,
        msg: Dict[str, Any],
    ) -> None:
        mtype = msg.get("type")

        if mtype == MSG_HELLO:
            self._handle_hello(server, host, addr, msg)

        elif mtype == MSG_INPUT:
            self._handle_input(world, msg)

        elif mtype == MSG_PING:
            server.send_raw(addr, {"type": MSG_PONG, "time": msg.get("time", 0)})

        elif mtype == MSG_DISCONNECT:
            peer_id = msg.get("peer_id")
            if isinstance(peer_id, str):
                host.peers.pop(peer_id, None)
                server.unregister_peer(peer_id)

    def _handle_hello(
        self,
        server: NetServer,
        host: NetHostState,
        addr: Address,
        msg: Dict[str, Any],
    ) -> None:
        # Version check
        if int(msg.get("protocol", -1)) != PROTOCOL_VERSION:
            server.send_raw(addr, {
                "type": MSG_JOIN_DENY,
                "reason": "protocol_mismatch",
            })
            return

        # Deny if full
        if len(host.peers) >= host.max_clients:
            server.send_raw(addr, {
                "type": MSG_JOIN_DENY,
                "reason": "full",
            })
            return

        # Assign a new peer id
        base = "peer"
        index = 1
        while f"{base}:{index}" in host.peers:
            index += 1
        peer_id = f"{base}:{index}"

        # Remember mapping
        host.peers[peer_id] = addr
        server.register_peer(peer_id, addr)

        # Send welcome
        server.send_raw(addr, {
            "type": MSG_WELCOME,
            "protocol": PROTOCOL_VERSION,
            "peer_id": peer_id,
        })

    def _handle_input(self, world, msg: Dict[str, Any]) -> None:
        peer_id = msg.get("peer_id")
        intent_data = msg.get("intent", {})
        if not isinstance(peer_id, str):
            return

        # Map remote input into the owner entity's Intent/InputState
        for _eid, comps in world.query(PlayerTag, Owner, Intent, InputState):
            owner: Owner = comps[Owner]
            if owner.peer_id != peer_id:
                continue

            intent: Intent = comps[Intent]

            # Movement axes
            intent.move_x = float(intent_data.get("move_x", 0.0))
            intent.move_y = float(intent_data.get("move_y", 0.0))
            intent.facing = intent_data.get("facing", intent.facing)

            # Actions
            intent.basic_atk = bool(intent_data.get("basic_atk", False))
            intent.basic_atk_held = bool(intent_data.get("basic_atk_held", False))
            intent.dash = bool(intent_data.get("dash", False))
            intent.special_atk = bool(intent_data.get("special_atk", False))

            break
