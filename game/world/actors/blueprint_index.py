# AUTHORED BY: SCOTT PETTY
# contains load function used to read heroes.json and enemies.json
# stores the information in global variables

# the .json data is used as blueprints for how we map components to entities

import json

HERO_BP = {}
ENEMY_BP = {}

def load(path_heroes: str, path_enemies: str):
    global HERO_BP, ENEMY_BP
    with open(path_heroes, "r", encoding="utf-8") as f: HERO_BP = json.load(f)
    with open(path_enemies, "r", encoding="utf-8") as f: ENEMY_BP = json.load(f)

# returns relevant entity-component blueprint data depending on id.
# the id is the outermost string in each datablock in the .json file.
# example: "hero.knight", "enemy.chort", ...
def hero(id: str) -> dict: return HERO_BP[id]
def enemy(id: str) -> dict: return ENEMY_BP[id]