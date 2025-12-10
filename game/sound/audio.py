# AUTHORED BY: Scott Petty

# central audio manager
# used by SoundSystem

import os
import random
from typing import Dict, List, Optional

import pygame

_initialized = False

_sound_groups: Dict[str, List[pygame.mixer.Sound]] = {}
_group_min_interval_ms: Dict[str, int] = {}
_group_last_play_ms: Dict[str, int] = {}

_current_scene_kind = None
_current_music_intro = None
_current_music_loop = None
_music_is_playing_intro = False

_current_music_id: Optional[str] = None

# internal helpers #############################################################

# make sure pygame and sound mixer are initialized
def _init_mixer_if_needed() -> None:
    global _initialized
    if _initialized:
        return
    
    if not pygame.get_init():
        return
    
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except Exception as e:
            print("[audio] pygame.mixer.init() failed:", e)
            return
        
    _initialized = True

# register a sound group
def register_group(
    group_id: str,
    file_paths: List[str],
    *,
    min_interval_ms: int = 0,
    volume: float = 1.0,
) -> None:
    _init_mixer_if_needed()
    if not _initialized:
        return
    
    sounds: List[pygame.mixer.Sound] = []
    for path in file_paths:
        if not os.path.isfile(path):
            print(f"[audio] File not found: {path}")
            continue

        try:
            snd = pygame.mixer.Sound(path)
            snd.set_volume(max(0.0, min(1.0, float(volume))))
            sounds.append(snd)
        except Exception as e:
            print(f"[audio] Failed to load sound '{path}': {e}")

    if not sounds:
        return
    
    _sound_groups[group_id] = sounds
    _group_min_interval_ms[group_id] = max(0, int(min_interval_ms))
    _group_last_play_ms.setdefault(group_id, 0)

# sfx registration and playback ####################################################

# play a random sound from the given group
def play_sfx_group(group_id: str, *, volume: Optional[float] = None) -> None:
    _init_mixer_if_needed()
    if not _initialized:
        return
    
    sounds = _sound_groups.get(group_id)
    if not sounds:
        return
    
    now = pygame.time.get_ticks()
    min_interval = _group_min_interval_ms.get(group_id, 0)
    last = _group_last_play_ms.get(group_id, 0)
    if min_interval and (now - last) < min_interval:
        return
    
    snd = random.choice(sounds)
    if volume is not None:
        snd.set_volume(max(0.0, min(1.0, float(volume))))

    snd.play()
    _group_last_play_ms[group_id] = now

# music control #####################################################################

SCENE_MUSIC_CONFIG: dict[str, Dict[str, Optional[str]]] = {
    "title": {
        "intro": None,
        "loop": "assets/sounds/music/title/cinematic-halloween-synthesizer-music-248525.mp3",
    },
    "hub": {
        "intro": "assets/sounds/music/hub/07. Spirits Forest (intro).mp3",
        "loop": "assets/sounds/music/hub/07. Spirits Forest (loop).mp3",
    },
    "dungeon": {
        "intro": None,
        "loop": "assets/sounds/music/dungeon/05. Long Journey.mp3"
    },
}

# play or change background music using an exact path
# music will fade out if the path is None
def _set_music_track(
        music_path: Optional[str],
        *,
        loop: int = -1,
        fade_ms: int = 500,
        volume: float = 0.6,
) -> None:
    _init_mixer_if_needed()
    if not _initialized:
        return
    
    global _current_music_id

    if not music_path:
        pygame.mixer.music.fadeout(max(0, fade_ms))
        _current_music_id = None
        return
    
    # don't restart same track over and over
    if _current_music_id == music_path:
        return
    
    try:
        pygame.mixer.music.fadeout(max(0, fade_ms))
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(max(0.0, min(0.36, float(volume))))
        pygame.mixer.music.play(loops=loop, fade_ms=max(0, fade_ms))
        _current_music_id = music_path
    except Exception as e:
        print(f"[audio] Failed to start music '{music_path}': {e}")
        _current_music_id = None

# select music based on scene kind
def set_scene_music(
    scene_kind: str,
    *,
    fade_ms: int = 500,
    volume: float = 0.6,
) -> None:
    _init_mixer_if_needed()
    if not _initialized:
        return

    global _current_scene_kind, _current_scene_phase

    cfg = SCENE_MUSIC_CONFIG.get(scene_kind)
    if cfg is None:
        # Unknown scene kind -> fade out music
        _set_music_track(None, loop=0, fade_ms=fade_ms, volume=volume)
        _current_scene_kind = None
        _current_scene_phase = "none"
        return

    intro_path = cfg.get("intro")
    loop_path = cfg.get("loop")

    # Scene changed (e.g., title -> hub, hub -> dungeon)
    if scene_kind != _current_scene_kind:
        _current_scene_kind = scene_kind

        # If we have an intro, play that once first
        if intro_path:
            _current_scene_phase = "intro"
            _set_music_track(
                intro_path,
                loop=0,         # play once
                fade_ms=fade_ms,
                volume=volume,
            )
        else:
            # No intro: go straight into loop
            _current_scene_phase = "loop"
            _set_music_track(
                loop_path,
                loop=-1,        # infinite loop
                fade_ms=fade_ms,
                volume=volume,
            )
        return

    # Same scene as last frame
    if _current_scene_phase == "intro":
        # If intro finished, switch to loop (if any)
        if not pygame.mixer.music.get_busy():
            if loop_path:
                _current_scene_phase = "loop"
                _set_music_track(
                    loop_path,
                    loop=-1,
                    fade_ms=200,
                    volume=volume,
                )
        # else: intro is still playing, nothing to do
    elif _current_scene_phase == "loop":
        # Already looping the correct scene track; nothing to do.
        pass
    else:
        # Phase "none" but we have a cfg: fallback to loop
        _current_scene_phase = "loop"
        _set_music_track(
            loop_path,
            loop=-1,
            fade_ms=fade_ms,
            volume=volume,
        )

# register sound groups using asset paths
# this gets called once after pygame.init()
def bootstrap_sounds() -> None:
    # player sounds ######################################
    register_group(
        "player.sword_swing",
        [
            "assets/sounds/player/sword_swing/1.wav",
            "assets/sounds/player/sword_swing/2.wav",
            "assets/sounds/player/sword_swing/3.wav",
            "assets/sounds/player/sword_swing/4.wav",
            "assets/sounds/player/sword_swing/5.wav",
            "assets/sounds/player/sword_swing/6.wav",
            "assets/sounds/player/sword_swing/7.wav",
            "assets/sounds/player/sword_swing/8.wav",
        ],
        min_interval_ms=30,
        volume=0.9,
    )

    register_group(
        "player.dash",
        [
            "assets/sounds/player/dash/Woosh_1.ogg",
            "assets/sounds/player/dash/Woosh_2.ogg",
        ],
        min_interval_ms=400,
        volume=0.7
    )

    register_group(
        "player.death",
        [
            "assets/sounds/player/death/cartoon-trombone-sound-effect-241387.mp3"
        ],
        min_interval_ms = 500,
        volume = 0.5
    )   

    # enemy aggro sounds ###################################################
    register_group(
        "enemy.aggro.big",
        [
            "assets/sounds/enemy/big/grunt/Noise_Big_Monster_1.wav",
            "assets/sounds/enemy/big/grunt/Noise_Big_Monster_1.wav",
            "assets/sounds/enemy/big/grunt/Noise_Big_Monster_1.wav",
        ],
        min_interval_ms=150,
        volume=1.0,
    )

    register_group(
        "enemy.aggro.medium",
        [
            "assets/sounds/enemy/medium/grunt/Noise_Medium_Monster_1.wav",
            "assets/sounds/enemy/medium/grunt/Noise_Medium_Monster_2.wav",
            "assets/sounds/enemy/medium/grunt/Noise_Medium_Monster_3.wav",
        ],
        min_interval_ms=150,
        volume=0.8,
    )

    register_group(
        "enemy.aggro.small",
        [
            "assets/sounds/enemy/small/grunt/Noise_Small_Monster_1.wav",
            "assets/sounds/enemy/small/grunt/Noise_Small_Monster_2.wav",
            "assets/sounds/enemy/small/grunt/Noise_Small_Monster_3.wav",
        ],
        min_interval_ms=150,
        volume=0.7,
    )

    register_group(
        "enemy.aggro.tiny",
        [
            "assets/sounds/enemy/tiny/grunt/Noise_Tiny_Monster_1.wav",
            "assets/sounds/enemy/tiny/grunt/Noise_Tiny_Monster_2.wav",
            "assets/sounds/enemy/tiny/grunt/Noise_Tiny_Monster_3.wav",
        ],
        min_interval_ms=150,
        volume=0.7,
    )

    # enemy death sounds ############################################################
    register_group(
        "enemy.death.big",
        [
            "assets/sounds/enemy/big/death/Noise_Big_Monster_Down_1.wav",
            "assets/sounds/enemy/big/death/Noise_Big_Monster_Down_2.wav",
            "assets/sounds/enemy/big/death/Noise_Big_Monster_Down_3.wav",
        ],
        min_interval_ms=50,
        volume=1.0,
    )

    register_group(
        "enemy.death.medium",
        [
            "assets/sounds/enemy/medium/death/Noise_Medium_Monster_Down_1.wav",
            "assets/sounds/enemy/medium/death/Noise_Medium_Monster_Down_2.wav",
            "assets/sounds/enemy/medium/death/Noise_Medium_Monster_Down_3.wav",
        ],
        min_interval_ms=50,
        volume=0.9,
    )

    register_group(
        "enemy.death.small",
        [
            "assets/sounds/enemy/small/death/Noise_Small_Monster_Down_1.wav",
            "assets/sounds/enemy/small/death/Noise_Small_Monster_Down_2.wav",
            "assets/sounds/enemy/small/death/Noise_Small_Monster_Down_3.wav",
        ],
        min_interval_ms=50,
        volume=0.8,
    )

    register_group(
        "enemy.death.tiny",
        [
            "assets/sounds/enemy/tiny/death/Noise_Tiny_Monster_Down_1.wav",
            "assets/sounds/enemy/tiny/death/Noise_Tiny_Monster_Down_2.wav",
            "assets/sounds/enemy/tiny/death/Noise_Tiny_Monster_Down_3.wav",
        ],
        min_interval_ms=50,
        volume=0.8,
    )

    # shared damage sounds #######################################################
    register_group(
        "misc.damage",
        [
            "assets/sounds/misc/damage/1.wav",
            "assets/sounds/misc/damage/2.wav",
            "assets/sounds/misc/damage/3.wav",
            "assets/sounds/misc/damage/4.wav",
        ],
        min_interval_ms=40,
        volume=0.8,
    )

    # chest open sound #############################################################
    register_group(
        "misc.chest_open",
        [
            "assets/sounds/misc/chest_open/SpecialFX_Magic_2.wav",
        ],
        min_interval_ms=300,
        volume=0.9,
    )

    # menu sounds ##################################################################
    register_group(
        "ui.menu_item_change",
        [
            "assets/sounds/ui/menu_item_change/UI - Button Select 1.wav",
        ],
        min_interval_ms=60,
        volume=0.4,
    )

    register_group(
        "ui.ready_up",
        [
            "assets/sounds/ui/ready_up/UI - Button 01.wav"
        ],
        min_interval_ms=60,
        volume=0.9,
    )

    # other sounds ###############################################################################
    register_group(
        "misc.transition",
        [
            "assets/sounds/misc/transition/Transportation - Move 01.wav"
        ],
        min_interval_ms=60,
        volume=0.5,
    )