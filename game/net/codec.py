import json

def encode_packet(msg: dict) -> bytes:
    # single-packet JSON
    return json.dumps(msg).encode("utf-8")

def decode_packet(data: bytes):
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None
