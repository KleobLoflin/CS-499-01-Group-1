# AUTHORED BY: Scott Petty, Cole Herzog
# Converts Python dict messages <-> bytes using JSON over UDP.

from __future__ import annotations
import json
from typing import Any, Dict

# Encode message dict into bytes to send over UDP using a jSON representation
def encode_message(message: Dict[str, Any]) -> bytes:
    return json.dumps(message, separators=(",", ":")).encode("utf-8")


# Decode bytes recieved from the network back into a dict
def decode_message(data: bytes) -> Dict[str, Any]:
    text = data.decode("utf-8")
    return json.loads(text)
