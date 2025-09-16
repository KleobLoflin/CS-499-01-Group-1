import json

HERO_BP = {}
ENEMY_BP = {}

def load(path_heroes: str, path_enemies: str):
    global HERO_BP, ENEMY_BP
    with open(path_heroes, "r", encoding="utf-8") as f: HERO_BP = json.load(f)
    with open(path_enemies, "r", encoding="utf-8") as f: ENEMY_BP = json.load(f)

def hero(id: str) -> dict: return HERO_BP[id]
def enemy(id: str) -> dict: return ENEMY_BP[id]