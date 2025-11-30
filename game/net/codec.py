# game/net/codec.py

import json

def encode_packet(msg: dict) -> bytes:
    """
    Encode a message dict into bytes for UDP.
    Right now we use JSON; could be swapped to msgpack, etc. later.
    """
    return json.dumps(msg).encode("utf-8")


def decode_packet(data: bytes):
    """
    Decode bytes into a message dict.
    Returns None on failure.
    """
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None
