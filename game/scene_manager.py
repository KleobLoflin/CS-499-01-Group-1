# Class: SceneManager

# controls which scene is active (Menu -> Hub -> Dungeon)
# possible fields: stack: list[Scene]
# possible methods: set(scene), push(scene), pop(), update(dt), draw(surface), handle_event(ev)
# This class controls switching scenes and keeps it decoupled from game logic