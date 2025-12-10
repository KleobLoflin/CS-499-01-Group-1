# AUTHORED BY: Scott Petty
# helper to get enemy size from AI
# NO LONGER USED, add ai.size for all enemies in json

from game.world.components import AI

# Exact-name mapping 
_EXACT_SIZE_MAP = {
    "boss": "big",
    "big_zombie": "medium",
    "chort": "small",
    "goblin": "tiny",
}

# Keyword-based fallback
_KEYWORD_SIZE_RULES = [
    ("boss",   "big"),
    ("big_zombie", "medium"),
    ("zombie big", "medium"),  
    ("chort",  "small"),
    ("goblin", "tiny"),
]

# get lower case enemy string
def _normalize_enemy_type(ai: AI) -> str:
    raw = getattr(ai, "enemy_type", None) or getattr(ai, "kind", "")
    et = str(raw).lower().strip()

    # Strip simple prefixes 
    for prefix in ("enemy.", "mob.", "npc."):
        if et.startswith(prefix):
            et = et[len(prefix):]
            break
    return et


# gets enemy size
def infer_enemy_size(ai: AI) -> str:
    et = _normalize_enemy_type(ai)

    # Exact-name mapping 
    if et in _EXACT_SIZE_MAP:
        return _EXACT_SIZE_MAP[et]

    # Keyword rules 
    words = et.split()
    joined = " ".join(words)
    for key, size in _KEYWORD_SIZE_RULES:
        # Support multi-word keys like "zombie big"
        parts = key.split()
        if all(p in joined for p in parts):
            return size

    # Fallback
    return "small"