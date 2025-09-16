# Class: Resources

# loads/caches images, atlases, fonts, audio.
# serves animation clips/frames

# possible methods: load_*, get_image(id), get_clip(atlas_id, clip, frame)
# the point of this class is to be a single source for loading assets to prevent double loading

import json, os, pygame

images = {}     # path -> surface
atlases = {}    # atlas_id ->

def image(path: str) -> pygame.Surface:
    surface = images.get(path)
    if surface is None:
        surface = pygame.image.load(path).convert_alpha()
        images[path] = surface
    return surface

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

def atlas_has(atlas_id: str, clip: str) -> bool:
    a = atlases.get(atlas_id)
    return bool(a and clip in a["clips"])

def clip_info(atlas_id: str, clip: str):

    # returns frames, fps, loop, mirror_x, origin
    a = atlases.get(atlas_id)
    if not a or clip not in a["clips"]:
        return [], 0, True, False, (0, 0)
    
    cm = a["clips"][clip]
    return cm["frames"], cm["fps"], cm["loop"], a["mirror_x"], a["origin"]