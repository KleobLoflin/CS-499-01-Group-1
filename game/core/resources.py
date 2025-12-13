# AUTHORED BY: Scott Petty
# contains functions for loading sprite images and animation clip data
# will possibly contain functions for loading fonts and audio in the future

# serves animation clips/frames

# the point of this script is to be a single source for loading assets to prevent double loading

import json, os, pygame
from game.core.paths import resource_path

images = {}     # path -> surface
atlases = {}    # atlas ids -> graphical metadata

# loads an image from a path and used to create a pygame surface.
# stores the surface in the images dictionary as well as returns the surface.
def image(path: str) -> pygame.Surface:
    surface = images.get(resource_path(path))
    if surface is None:
        surface = pygame.image.load(resource_path(path)).convert_alpha()
        images[resource_path(path)] = surface
    return surface

# reads and loads atlas data from a .json file
# stores this data in the atlases dictionary
def load_atlases(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for atlas_id, meta in data.get("atlases", {}).items():
        mirror_x = bool(meta.get("mirror_x", False))
        origin = tuple(meta.get("origin", [0, 0]))
        clips_meta = {}

        for clip_name, clip in meta.get("clips", {}).items():
            frames = [image(p) for p in clip.get("frames", [])]
            fps = int(clip.get("fps", 8))
            loop = bool(clip.get("loop", True))
            clips_meta[clip_name] = {"frames": frames, "fps": fps, "loop": loop}
        
        atlases[atlas_id] = {"mirror_x": mirror_x, "origin": origin, "clips": clips_meta}

# checks if an atlas id has an associated animation clip
def atlas_has(atlas_id: str, clip: str) -> bool:
    a = atlases.get(atlas_id)
    return bool(a and clip in a["clips"])

# returns animation clip data given an atlas id and clip name
def clip_info(atlas_id: str, clip: str):
    a = atlases.get(atlas_id)
    if not a or clip not in a["clips"]:
        return [], 0, True, False, (0, 0)
    
    cm = a["clips"][clip]
    return cm["frames"], cm["fps"], cm["loop"], a["mirror_x"], a["origin"]