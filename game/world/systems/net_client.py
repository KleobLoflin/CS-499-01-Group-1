# game/world/systems/net_client.py
#
# NetClientSystem:
#   - Runs ONLY on clients (NetIdentity.role == "CLIENT").
#   - Sends local input at a fixed rate.
#   - Receives world snapshots from host and applies them.

from __future__ import annotations

from typing import Any, Dict

from game.world.components import (
    NetIdentity,
    NetClientState,
    PlayerTag,
    Owner,
    LocalControlled,
    Intent,
    InputState,
)
from game.net.client import NetClient
from game.net.protocol import (
    PROTOCOL_VERSION,
    MSG_HELLO,
    MSG_WELCOME,
    MSG_INPUT,
    MSG_SNAPSHOT,
    MSG_PING,
    MSG_PONG,
    MSG_START_GAME,
)
from game.net.snapshots import apply_world_snapshot


class NetClientSystem:
    # uses NetClientState component to talk to the underlying NetClient socket wrapper.

    def update(self, world, dt: float) -> None:
        # Locate network singleton
        net_id: NetIdentity | None = None
        client_state: NetClientState | None = None

        for _eid, comps in world.query(NetIdentity, NetClientState):
            net_id = comps[NetIdentity]
            client_state = comps[NetClientState]
            break

        if net_id is None or client_state is None:
            return
        if net_id.role != "CLIENT":
            return
        if client_state.client is None:
            return

        client: NetClient = client_state.client

        # Send local input at a fixed rate
        client_state.accumulator += dt
        while client_state.accumulator >= client_state.send_interval:
            client_state.accumulator -= client_state.send_interval
            client_state.tick += 1

            payload = self._build_local_input_payload(world, net_id.my_peer_id)
            if payload is not None:
                msg: Dict[str, Any] = {
                    "type": MSG_INPUT,
                    "protocol": PROTOCOL_VERSION,
                    "peer_id": net_id.my_peer_id,
                    "tick": client_state.tick,
                    "intent": payload,
                }
                client.send(msg)

        # Receive and handle incoming messages
        for msg in client.recv_all():
            self._handle_message(world, net_id, client_state, msg)

    # internals ###############################################################

    # Find the LocalControlled + Owner(peer_id=my_peer_id) entity and convert its Intent to a wire-friendly dict
    def _build_local_input_payload(self, world, my_peer_id: str) -> Dict[str, Any] | None:
        for _eid, comps in world.query(PlayerTag, Owner, LocalControlled, Intent, InputState):
            owner: Owner = comps[Owner]
            if owner.peer_id != my_peer_id:
                continue

            intent: Intent = comps[Intent]
            return {
                "move_x": intent.move_x,
                "move_y": intent.move_y,
                "facing": intent.facing,
                "basic_atk": intent.basic_atk,
                "basic_atk_held": intent.basic_atk_held,
                "dash": intent.dash,
                "special_atk": intent.special_atk,
            }

        return None

    def _handle_message(
        self,
        world,
        net_id: NetIdentity,
        client_state: NetClientState,
        msg: Dict[str, Any],
    ) -> None:
        mtype = msg.get("type")

        if mtype == MSG_WELCOME:
            # Host confirms and possibly overrides our peer id.
            peer_id = msg.get("peer_id")
            if isinstance(peer_id, str):
                net_id.my_peer_id = peer_id

        elif mtype == MSG_SNAPSHOT:
            # Directly applies snapshot
            # probably need to implement buffering and interpolation later
            if int(msg.get("protocol", PROTOCOL_VERSION)) != PROTOCOL_VERSION:
                return
            tick = int(msg.get("tick", 0))
            if tick <= client_state.last_snapshot_tick:
                return
            client_state.last_snapshot_tick = tick

            apply_world_snapshot(world, msg, net_id.my_peer_id)

        elif mtype == MSG_PING:
            # echo ping → pong
            client_state.client.send({"type": MSG_PONG, "time": msg.get("time", 0)})

        elif mtype == MSG_START_GAME:
            # START_GAME now handled in HubScene._client_net_pump
            return
