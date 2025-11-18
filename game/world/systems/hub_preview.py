# game/world/systems/hub_preview.py
#
# Keeps lobby slot preview sprites in sync with LobbySlot state.
# For every occupied LobbySlot it spawns (or updates) a hero entity that:
#   - uses the correct hero blueprint
#   - plays the idle animation
#   - sits in the correct column on the screen
#
# for use with hub_scene only

from game.core.config import Config
from game.world.components import (
    LobbyState, LobbySlot,
    Sprite, Transform, AnimationState, Facing
)
from game.world.actors.hero_factory import create as create_hero


class HubPreviewSystem:
    def update(self, world, dt: float) -> None:
        # Find LobbyState to get character_catalog
        lobby = None
        for _, comps in world.query(LobbyState):
            lobby = comps[LobbyState]
            break

        if lobby is None:
            return

        catalog = lobby.character_catalog
        if not catalog:
            return

        columns = 5

        def slot_pos(index: int) -> tuple[float, float]:
            x = (Config.WINDOW_W / (columns + 1)) * (index + 1)
            y = Config.WINDOW_H / 2
            return x, y

        # ---- PHASE 1: snapshot slots so we don't mutate world during query ----
        slots: list[tuple[int, LobbySlot]] = []
        for slot_eid, comps in world.query(LobbySlot):
            slots.append((slot_eid, comps[LobbySlot]))

        # ---- PHASE 2: now it's safe to delete/create entities -----------------
        for slot_eid, slot in slots:
            # If the slot has no player, kill any preview and continue
            if slot.peer_id is None and not slot.is_local:
                if slot.preview_eid is not None:
                    world.delete_entity(slot.preview_eid)
                    slot.preview_eid = None
                continue

            # Clamp/normalize selected_char_index
            idx = slot.selected_char_index % len(catalog)
            hero_key = catalog[idx]         # e.g. "hero.knight_blue"

            # If we already have a preview entity, check if it matches this hero
            if slot.preview_eid is not None:
                preview_comps = world.components_of(slot.preview_eid)
                spr = preview_comps.get(Sprite)
                tr = preview_comps.get(Transform)

                if spr is not None and spr.atlas_id == hero_key:
                    # Same hero, just update position and continue
                    if tr is not None:
                        tr.x, tr.y = slot_pos(slot.index)
                    continue

                # Wrong hero or missing sprite -> delete and recreate
                world.delete_entity(slot.preview_eid)
                slot.preview_eid = None

            # Need to create a new preview entity for this slot
            archetype = hero_key.split(".", 1)[1]  # "knight_blue" from "hero.knight_blue"
            x, y = slot_pos(slot.index)

            eid = create_hero(
                world,
                archetype=archetype,
                owner_client_id=slot.peer_id,
                pos=(x, y),
            )

            # Force idle animation, facing down by default
            comps2 = world.components_of(eid)
            anim = comps2.get(AnimationState)
            if anim is not None:
                anim.clip = "idle"
                anim.frame = 0
                anim.time = 0.0
                anim.changed = True

            face = comps2.get(Facing)
            if face is not None and face.direction is not "down":
                face.direction = "down"

            slot.preview_eid = eid

