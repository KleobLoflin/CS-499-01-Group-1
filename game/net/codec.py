import json

def encode(msg: dict) -> bytes:
    return (json.dumps(msg) + "\n").encode()

def decode(buffer: str):
    # yields complete messages from buffer
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        if line.strip():
            yield json.loads(line)
    return buffer
